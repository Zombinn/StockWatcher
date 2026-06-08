import { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Alert, Modal, Select, InputNumber, Space, Statistic, Row, Col, Spin, Empty, Typography, message, Input } from 'antd';
import { ReloadOutlined, PlusOutlined, DeleteOutlined, CheckOutlined, BellOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;


const RULE_TYPE_LABELS: Record<string, string> = {
  price_above: '价格上穿', price_below: '价格下穿', change_pct: '涨跌幅(%)', volume: '成交量(万手)',
};

export default function AlertsPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<{ code: string; price_above?: number; price_below?: number; change_pct?: number; volume?: number }>({ code: "" });

  const load = async () => {
    setLoading(true); setError('');
    try { const d = await api.getAlerts(); setData(d); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    const code = form.code.trim();
    if (!code) { message.warning('请输入股票代码'); return; }
    const dims: { t: string; v: number | undefined }[] = [
      { t: 'price_above', v: form.price_above },
      { t: 'price_below', v: form.price_below },
      { t: 'change_pct', v: form.change_pct },
      { t: 'volume', v: form.volume },
    ];
    let count = 0;
    for (const d of dims) {
      if (d.v != null) { await api.addAlert(code, d.t, d.v, code); count++; }
    }
    setModalOpen(false); setForm({ code: '' });
    message.success(`已保存 ${code} 的 ${count || 0} 个告警维度`);
    load();
  };

  const remove = async (id: string) => { await api.removeAlert(id); load(); };

  const check = async () => {
    const d = await api.checkAlerts();
    if (d.triggered > 0) load();
  };

  const ruleColumns = [
    { title: '代码', dataIndex: 'code', width: 90,
      render: (v: string) => <Text strong style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}>{v}</Text>,
    },
    { title: '名称', dataIndex: 'name', width: 100,
      render: (v: string) => <Text style={{ color: '#64748b' }}>{v || '-'}</Text>,
    },
    { title: '上穿', dataIndex: 'price_above', width: 80, align: 'right' as const,
      render: (v: number | null) => v != null ? <span style={{ fontWeight: 500, color: '#e53935' }}>{v}</span> : <Text type="secondary">-</Text>,
    },
    { title: '下穿', dataIndex: 'price_below', width: 80, align: 'right' as const,
      render: (v: number | null) => v != null ? <span style={{ fontWeight: 500, color: '#43a047' }}>{v}</span> : <Text type="secondary">-</Text>,
    },
    { title: '涨跌%', dataIndex: 'change_pct', width: 80, align: 'right' as const,
      render: (v: number | null) => v != null ? <span style={{ fontWeight: 500, color: '#f9a825' }}>{v}%</span> : <Text type="secondary">-</Text>,
    },
    { title: '成交(万手)', dataIndex: 'volume', width: 95, align: 'right' as const,
      render: (v: number | null) => v != null ? <span style={{ fontWeight: 500 }}>{v}</span> : <Text type="secondary">-</Text>,
    },
    { title: '操作', width: 70,
      render: (_: any, r: any) => <Button danger size="small" icon={<DeleteOutlined />} onClick={(e: any) => { e.stopPropagation(); remove(r.code); }} />,
    },
  ];

  // Merge multi-type rules into code-keyed rows
  const groupedRules = (data?.rules || []).map((r: any) => ({
    code: r.code, name: r.name || r.code,
    price_above: r.price_above ?? null,
    price_below: r.price_below ?? null,
    change_pct: r.change_pct ?? null,
    volume: r.volume ?? null,
    enabled: r.enabled,
    id: r.code,
  }));

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>告警管理</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>价格监控与事件通知</Text>
        </div>
        <Space>
          <Button icon={<CheckOutlined />} onClick={check}>检查</Button>
          <Button icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加规则</Button>
          <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={load}>刷新</Button>
        </Space>
      </div>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <div className="loading-breathe" style={{ marginBottom: 16 }}>
            <div className="dot-pulse" style={{ margin: '0 auto' }} />
          </div>
          <Text className="loading-text" style={{ fontSize: 13 }}>正在加载...</Text>
        </div>
      ) : data ? (
        <>
          {data.stats && (
            <Row gutter={12} style={{ marginBottom: 16 }}>
              <Col span={6}><Card className="stat-card" size="small"><Statistic title={<span style={{ color: '#64748b' }}>规则</span>} value={data.stats.total_rules} valueStyle={{ fontWeight: 600, color: '#1a1a2e' }} /></Card></Col>
              <Col span={6}><Card className="stat-card" size="small"><Statistic title={<span style={{ color: '#64748b' }}>启用</span>} value={data.stats.enabled_rules} valueStyle={{ color: '#43a047', fontWeight: 600 }} /></Card></Col>
              <Col span={6}><Card className="stat-card" size="small"><Statistic title={<span style={{ color: '#64748b' }}>事件</span>} value={data.stats.total_events} valueStyle={{ fontWeight: 600, color: '#1a1a2e' }} /></Card></Col>
              <Col span={6}><Card className="stat-card" size="small"><Statistic title={<span style={{ color: '#64748b' }}>未通知</span>} value={data.stats.recent_events} valueStyle={{ color: '#f9a825', fontWeight: 600 }} /></Card></Col>
            </Row>
          )}
          <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>告警规则</span>} style={{ marginBottom: 16 }}>
            {data.rules?.length > 0 ? (
              <Table dataSource={groupedRules} columns={ruleColumns} rowKey="code" pagination={{ defaultPageSize: 10, pageSizeOptions: [10, 20, 50], showSizeChanger: true }} size="small"
                onRow={(record: any) => ({
                  style: { cursor: 'pointer' },
                  onClick: () => {
                    setForm({
                      code: record.code,
                      price_above: record.price_above ?? undefined,
                      price_below: record.price_below ?? undefined,
                      change_pct: record.change_pct ?? undefined,
                      volume: record.volume ?? undefined,
                    });
                    setModalOpen(true);
                  },
                })} />
            ) : <Empty description="暂无告警规则" />}
          </Card>
          <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}><BellOutlined style={{ marginRight: 6, color: '#f5642a' }} />最近事件</span>}>
            {data.events?.length > 0 ? (
              <Table
                dataSource={data.events.slice(0, 10)}
                columns={[
                  { title: '时间', dataIndex: 'timestamp', width: 170,
                    render: (v: string) => {
                      const t = v?.slice(0, 19) || '-';
                      return <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: '#64748b' }}>{t}</span>;
                    },
                  },
                  { title: '消息', dataIndex: 'message' },
                ]}
                rowKey="timestamp"
                pagination={{ defaultPageSize: 10, pageSizeOptions: [10, 20, 50], showSizeChanger: true }}
                size="small"
              />
            ) : <Empty description="暂无告警事件" />}
          </Card>
        </>
      ) : (
        <Card className="glass-card"><Empty description="暂无数据" /></Card>
      )}

      <Modal title={<>添加告警规则 - {form.code || '输入代码'}</>} open={modalOpen}
        onOk={add} onCancel={() => { setModalOpen(false); setForm({ code: '' }); }}
        okText="保存" cancelText="取消" width={460}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
          <div>
            <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>股票代码</div>
            <Input placeholder="输入股票代码，如 600519 / AAPL / 0700.HK"
              value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {(['price_above', 'price_below', 'change_pct', 'volume'] as const).map(key => (
              <div key={key}>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>{RULE_TYPE_LABELS[key]}</div>
                <InputNumber placeholder="不填" style={{ width: '100%' }} min={0}
                  step={key === 'volume' ? 1 : key === 'price_above' || key === 'price_below' ? 0.01 : 0.1}
                  value={form[key] ?? null}
                  onChange={v => setForm({ ...form, [key]: v ?? undefined })} />
              </div>
            ))}
          </div>
          <Text type="secondary" style={{ fontSize: 11 }}>同股票四个维度可选填，至少填一个。不填则无此维度的告警。</Text>
        </div>
      </Modal>
    </div>
  );
}
