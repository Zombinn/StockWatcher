import { useState, useEffect } from 'react';
import { Card, Button, Input, Switch, Select, Spin, Space, Typography, message } from 'antd';
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

export default function ConfigPage() {
  const [sections, setSections] = useState<any[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<any>(null);
  // Track form changes
  const [formDirty, setFormDirty] = useState<Record<string, string>>({});

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

  if (loading) return <Spin size="large" style={{ display: 'flex', justifyContent: 'center', marginTop: 60 }} />;

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<SaveOutlined />} loading={saving} onClick={save}>保存配置</Button>
        <Button icon={<ReloadOutlined />} onClick={load}>刷新</Button>
      </Space>

      {status && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Text type="secondary">
            .env 文件: {status.exists ? '已存在' : '未创建'} | 可配置项: {status.configurable_fields} 项
          </Text>
        </Card>
      )}

      {sections.map(sec => (
        <Card key={sec.key} title={sec.label} style={{ marginBottom: 16 }}>
          {sec.fields.map((f: any) => {
            const val = formDirty[f.key] !== undefined ? formDirty[f.key] : (values[f.key] ?? f.default ?? '');
            return (
              <div key={f.key} style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 4, color: '#8899aa', fontSize: 13 }}>{f.label}</label>
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
                {f.description && <div style={{ color: '#5a6a7a', fontSize: 12, marginTop: 2 }}>{f.description}</div>}
              </div>
            );
          })}
        </Card>
      ))}
    </div>
  );
}
