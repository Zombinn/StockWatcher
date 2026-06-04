import { useState } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Tag, Alert, Typography, Modal, Input, InputNumber, Space } from 'antd';
import { ReloadOutlined, PlusOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

export default function PortfolioPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ code: '', quantity: 100, cost_price: 0 });

  const load = async () => {
    setLoading(true); setError('');
    try { const d = await api.getPortfolio(); setData(d.data); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const add = async () => {
    await api.addPosition(form.code, form.quantity, form.cost_price);
    setModalOpen(false);
    load();
  };

  const columns = [
    { title: '代码', dataIndex: 'code', width: 100 },
    { title: '名称', dataIndex: 'name', width: 120 },
    { title: '持仓', dataIndex: 'quantity', width: 80 },
    { title: '成本', dataIndex: 'cost_price', width: 90, render: (v: number) => v.toFixed(2) },
    { title: '现价', dataIndex: 'current_price', width: 90, render: (v: number) => v.toFixed(2) },
    { title: '市值', dataIndex: 'market_value', width: 100, render: (v: number) => v.toFixed(2) },
    {
      title: '盈亏', dataIndex: 'profit_pct', width: 90,
      render: (v: number) => <Tag color={v >= 0 ? 'red' : 'green'}>{v >= 0 ? '+' : ''}{v.toFixed(2)}%</Tag>,
    },
    { title: '占比', dataIndex: 'weight', width: 80, render: (v: number) => `${v.toFixed(1)}%` },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={load}>加载持仓</Button>
        <Button icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加</Button>
      </Space>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

      {data && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={8}><Card><Statistic title="总市值" value={data.total_market_value} precision={2} /></Card></Col>
            <Col xs={8}><Card><Statistic title="总收益" value={data.total_profit} precision={2}
              valueStyle={{ color: data.total_profit >= 0 ? '#ff4d4d' : '#00d4aa' }}
              suffix={<span style={{ fontSize: 14 }}>({data.total_profit_pct >= 0 ? '+' : ''}{data.total_profit_pct.toFixed(2)}%)</span>}
            /></Card></Col>
            <Col xs={8}><Card><Statistic title="风险评分" value={data.risk_score} suffix="/100"
              valueStyle={{ color: data.risk_score > 60 ? '#ff4d4d' : data.risk_score > 30 ? '#ffc107' : '#00d4aa' }}
            /></Card></Col>
          </Row>
          {data.suggestion && <Alert type="info" message={data.suggestion} showIcon style={{ marginBottom: 16 }} />}
          <Card title="持仓明细">
            <Table dataSource={data.positions} columns={columns} rowKey="code" pagination={false} size="small" />
          </Card>
        </>
      )}
      <Modal title="添加持仓" open={modalOpen} onOk={add} onCancel={() => setModalOpen(false)}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Input placeholder="股票代码" value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} />
          <InputNumber placeholder="数量" value={form.quantity} min={1} onChange={v => setForm({ ...form, quantity: v || 0 })} style={{ width: '100%' }} />
          <InputNumber placeholder="成本价" value={form.cost_price} min={0} step={0.01} onChange={v => setForm({ ...form, cost_price: v || 0 })} style={{ width: '100%' }} />
        </div>
      </Modal>
    </div>
  );
}
