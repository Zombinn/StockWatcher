import { useState } from 'react';
import { Card, Button, Table, Tag, Alert, Modal, Input, Select, InputNumber, Space, Statistic, Row, Col } from 'antd';
import { ReloadOutlined, PlusOutlined, DeleteOutlined, CheckOutlined } from '@ant-design/icons';
import { api } from '../api';

const ruleTypes = [
  { value: 'price_above', label: '价格上穿' },
  { value: 'price_below', label: '价格下穿' },
  { value: 'change_pct', label: '涨跌幅' },
  { value: 'volume', label: '成交量(万手)' },
];

export default function AlertsPage() {
  const [loading, setLoading] = useState(false);
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

  const add = async () => {
    await api.addAlert(form.code, form.rule_type, form.threshold, form.code);
    setModalOpen(false); load();
  };

  const remove = async (id: string) => { await api.removeAlert(id); load(); };

  const check = async () => {
    const d = await api.checkAlerts();
    if (d.triggered > 0) load();
  };

  const ruleColumns = [
    { title: '代码', dataIndex: 'code', width: 100 },
    { title: '类型', dataIndex: 'rule_type', width: 120, render: (v: string) => ruleTypes.find(r => r.value === v)?.label || v },
    { title: '阈值', dataIndex: 'threshold', width: 100 },
    { title: '状态', dataIndex: 'enabled', width: 80, render: (v: boolean) => v ? '✅' : '❌' },
    {
      title: '操作', width: 80,
      render: (_: any, r: any) => <Button danger size="small" icon={<DeleteOutlined />} onClick={() => remove(r.id)} />,
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={load}>加载告警</Button>
        <Button icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加规则</Button>
        <Button icon={<CheckOutlined />} onClick={check}>检查</Button>
      </Space>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

      {data?.stats && (
        <Row gutter={12} style={{ marginBottom: 16 }}>
          <Col span={6}><Card size="small"><Statistic title="规则" value={data.stats.total_rules} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="启用" value={data.stats.enabled_rules} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="事件" value={data.stats.total_events} /></Card></Col>
          <Col span={6}><Card size="small"><Statistic title="未通知" value={data.stats.recent_events} /></Card></Col>
        </Row>
      )}

      {data?.rules?.length > 0 && (
        <Card title="告警规则" style={{ marginBottom: 16 }}>
          <Table dataSource={data.rules} columns={ruleColumns} rowKey="id" pagination={false} size="small" />
        </Card>
      )}

      {data?.events?.length > 0 && (
        <Card title="最近事件">
          <Table
            dataSource={data.events.slice(0, 10)}
            columns={[
              { title: '时间', dataIndex: 'timestamp', render: (v: string) => v.slice(0, 19), width: 180 },
              { title: '消息', dataIndex: 'message' },
            ]}
            rowKey="timestamp"
            pagination={false}
            size="small"
          />
        </Card>
      )}

      <Modal title="添加告警规则" open={modalOpen} onOk={add} onCancel={() => setModalOpen(false)}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Input placeholder="股票代码" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} />
          <Select value={form.rule_type} onChange={v => setForm({ ...form, rule_type: v })} options={ruleTypes} />
          <InputNumber placeholder="阈值" value={form.threshold} min={0} step={0.1} onChange={v => setForm({ ...form, threshold: v || 0 })} style={{ width: '100%' }} />
        </div>
      </Modal>
    </div>
  );
}
