import { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Alert, Modal, Input, Select, InputNumber, Space, Statistic, Row, Col, Spin, Empty, Typography } from 'antd';
import { ReloadOutlined, PlusOutlined, DeleteOutlined, CheckOutlined, BellOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

const ruleTypes = [
  { value: 'price_above', label: '价格上穿' },
  { value: 'price_below', label: '价格下穿' },
  { value: 'change_pct', label: '涨跌幅' },
  { value: 'volume', label: '成交量(万手)' },
];

export default function AlertsPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ code: '', rule_type: 'price_above', threshold: 0 });

  const load = async () => {
    setLoading(true); setError('');
    try { const d = await api.getAlerts(); setData(d); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    await api.addAlert(form.code, form.rule_type, form.threshold, form.code);
    setModalOpen(false); setForm({ code: '', rule_type: 'price_above', threshold: 0 }); load();
  };

  const remove = async (id: string) => { await api.removeAlert(id); load(); };

  const check = async () => {
    const d = await api.checkAlerts();
    if (d.triggered > 0) load();
  };

  const ruleColumns = [
    { title: '代码', dataIndex: 'code', width: 90 },
    { title: '类型', dataIndex: 'rule_type', width: 110,
      render: (v: string) => <Tag style={{ borderRadius: 4, border: 'none', color: '#f5642a', background: 'rgba(245,100,42,0.08)' }}>{ruleTypes.find(r => r.value === v)?.label || v}</Tag>,
    },
    { title: '阈值', dataIndex: 'threshold', width: 90, align: 'right' as const,
      render: (v: number) => <span style={{ fontWeight: 500, fontFamily: "'JetBrains Mono', monospace", color: '#1a1a2e' }}>{v}</span>,
    },
    { title: '状态', dataIndex: 'enabled', width: 70,
      render: (v: boolean) => <Tag color={v ? 'success' : 'default'} style={{ borderRadius: 4 }}>{v ? '启用' : '停用'}</Tag>,
    },
    { title: '操作', width: 70,
      render: (_: any, r: any) => <Button danger size="small" icon={<DeleteOutlined />} onClick={() => remove(r.id)} />,
    },
  ];

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
              <Table dataSource={data.rules} columns={ruleColumns} rowKey="id" pagination={false} size="small" />
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
                pagination={false}
                size="small"
              />
            ) : <Empty description="暂无告警事件" />}
          </Card>
        </>
      ) : (
        <Card className="glass-card"><Empty description="暂无数据" /></Card>
      )}

      <Modal title="添加告警规则" open={modalOpen} onOk={add} onCancel={() => setModalOpen(false)}
        okText="添加" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
          <Input placeholder="股票代码" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} />
          <Select value={form.rule_type} onChange={v => setForm({ ...form, rule_type: v })} options={ruleTypes} />
          <InputNumber placeholder="阈值" value={form.threshold} min={0} step={0.1}
            onChange={v => setForm({ ...form, threshold: v || 0 })} style={{ width: '100%' }} />
        </div>
      </Modal>
    </div>
  );
}
