import { useState, useEffect } from 'react';
import { Card, Button, Input, Switch, Select, Space, Tag, Typography, message } from 'antd';
import { SaveOutlined, ReloadOutlined, SettingOutlined, RightOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

// 市场 → 颜色（与持仓页一致）
const MARKET_META: Record<string, { label: string; color: string }> = {
  A: { label: 'A股', color: 'blue' },
  HK: { label: '港股', color: 'purple' },
  US: { label: '美股', color: 'green' },
};

function goToPortfolio() {
  window.dispatchEvent(new CustomEvent('sw-navigate', { detail: 'portfolio' }));
}

export default function ConfigPage() {
  const [sections, setSections] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [formDirty, setFormDirty] = useState<Record<string, string>>({});
  const [watchlist, setWatchlist] = useState<any[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const [s, v] = await Promise.all([api.getConfigSections(), api.getConfigValues()]);
      setSections(s.sections);
      setValues(v.values);
      setStatus(v.status);
      setFormDirty({});
    } catch (e: any) {
      message.error('加载配置失败: ' + e.message);
    } finally { setLoading(false); }
    // 自选股列表只读展示，单独异步加载（带行情，可能较慢）
    api.getWatchlist().then(d => setWatchlist(d.data || [])).catch(() => {});
  };

  const save = async () => {
    setSaving(true);
    try {
      const res = await api.updateConfig(formDirty);
      message.success(res.message || '保存成功');
      if (res.restart_required) message.info('部分配置需重启服务生效');
      load();
    } catch (e: any) {
      message.error('保存失败: ' + e.message);
    } finally { setSaving(false); }
  };

  const setVal = (key: string, val: string) => {
    setFormDirty(prev => ({ ...prev, [key]: val }));
  };

  useEffect(() => { load(); }, []);

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 80 }}>
      <div className="loading-breathe" style={{ marginBottom: 16 }}>
        <div className="dot-pulse" style={{ margin: '0 auto' }} />
      </div>
      <Text type="secondary">加载配置中...</Text>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>系统配置</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>服务端参数管理</Text>
        </div>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={load}>刷新</Button>
          <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={save}>保存配置</Button>
        </Space>
      </div>

      {status && (
        <Card className="glass-card" size="small" style={{ marginBottom: 16 }}>
          <Space>
            <SettingOutlined style={{ color: '#f5642a' }} />
            <Text type="secondary">
              .env 文件: {status.exists ? '已存在' : '未创建'} | 可配置项: {status.configurable_fields} 项
            </Text>
          </Space>
        </Card>
      )}

      {sections.map(sec => (
        <Card key={sec.key} className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>{sec.label}</span>} style={{ marginBottom: 16 }}>
          {sec.fields.map((f: any) => {
            const val = formDirty[f.key] !== undefined ? formDirty[f.key] : (values[f.key] ?? f.default ?? '');

            // 自选股列表：只读展示（代码+名称，颜色区分市场），管理跳转持仓页
            if (f.key === 'STOCK_LIST') {
              return (
                <div key={f.key} style={{ marginBottom: 20 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <Space size={8} wrap>
                      <span style={{ color: '#64748b', fontSize: 13, fontWeight: 500 }}>{f.label}</span>
                      <Space size={4}>
                        {Object.values(MARKET_META).map(m => (
                          <Tag key={m.label} color={m.color} style={{ borderRadius: 4, border: 'none', margin: 0, fontSize: 11, lineHeight: '18px' }}>{m.label}</Tag>
                        ))}
                      </Space>
                    </Space>
                    <a onClick={goToPortfolio} style={{ color: '#f5642a', fontSize: 13, fontWeight: 500 }}>
                      去配置 <RightOutlined style={{ fontSize: 10 }} />
                    </a>
                  </div>
                  {watchlist.length > 0 ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {watchlist.map(w => {
                        const meta = MARKET_META[w.market] || { color: 'default' };
                        return (
                          <Tag key={w.code} color={meta.color}
                            style={{ borderRadius: 6, padding: '3px 10px', margin: 0, fontSize: 13, cursor: 'default' }}>
                            <span style={{ fontWeight: 600 }}>{w.code}</span>
                            {w.name && w.name !== w.code && <span style={{ marginLeft: 6, opacity: 0.85 }}>{w.name}</span>}
                          </Tag>
                        );
                      })}
                    </div>
                  ) : (
                    <Text type="secondary" style={{ fontSize: 13 }}>暂无自选股，点击「去配置」前往持仓页添加</Text>
                  )}
                  <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 6 }}>自选股已迁至持仓页统一管理（不再于此编辑）</div>
                </div>
              );
            }

            return (
              <div key={f.key} style={{ marginBottom: 20 }}>
                <label style={{ display: 'block', marginBottom: 4, color: '#64748b', fontSize: 13, fontWeight: 500 }}>{f.label}</label>
                {f.type === 'boolean' ? (
                  <Switch
                    checkedChildren="开启" unCheckedChildren="关闭"
                    checked={val === 'true'}
                    onChange={(v) => setVal(f.key, v ? 'true' : 'false')}
                  />
                ) : f.type === 'select' ? (
                  <Select
                    value={val}
                    onChange={(v) => setVal(f.key, v)}
                    options={(f.options || []).map((o: string) => ({ value: o, label: o }))}
                    style={{ width: 200 }}
                  />
                ) : f.type === 'multiline' || (typeof val === 'string' && val.length > 60) ? (
                  <Input.TextArea value={val} onChange={e => setVal(f.key, e.target.value)} rows={3} />
                ) : (
                  <Input
                    value={val}
                    onChange={e => setVal(f.key, e.target.value)}
                    type={f.type === 'password' ? 'password' : 'text'}
                    placeholder={f.description}
                  />
                )}
                {f.description && <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 2 }}>{f.description}</div>}
              </div>
            );
          })}
        </Card>
      ))}
    </div>
  );
}
