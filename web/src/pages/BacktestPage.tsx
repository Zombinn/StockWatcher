import { useState } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Tag, Alert, Input, Select, Space, Typography } from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

const strategies = [
  { value: 'ma_cross', label: '均线金叉' },
  { value: 'macd', label: 'MACD' },
  { value: 'rsi', label: 'RSI' },
  { value: 'bollinger', label: '布林带' },
];

export default function BacktestPage() {
  const [code, setCode] = useState('600519');
  const [strategy, setStrategy] = useState('ma_cross');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true); setError('');
    try { const d = await api.backtest(code, strategy); setData(d.data); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const tradeColumns = [
    { title: '日期', dataIndex: 'date', width: 110 },
    { title: '操作', dataIndex: 'action', width: 70, render: (v: string) => <Tag color={v === 'buy' ? 'red' : 'green'}>{v}</Tag> },
    { title: '价格', dataIndex: 'price', width: 90, render: (v: number) => v.toFixed(2) },
    { title: '数量', dataIndex: 'shares', width: 80 },
    { title: '金额', dataIndex: 'amount', width: 100, render: (v: number) => v.toFixed(2) },
    { title: '理由', dataIndex: 'reason' },
  ];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Input value={code} onChange={e => setCode(e.target.value)} style={{ width: 120 }} placeholder="股票代码" />
          <Select value={strategy} onChange={setStrategy} options={strategies} style={{ width: 130 }} />
          <Button type="primary" icon={<ExperimentOutlined />} loading={loading} onClick={run}>回测</Button>
        </Space>
      </Card>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

      {data && (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={12} md={6}><Card size="small"><Statistic title="初始资金" value={data.initial_capital} precision={2} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="最终价值" value={data.final_value} precision={2}
              valueStyle={{ color: data.total_return >= 0 ? '#ff4d4d' : '#00d4aa' }} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="总收益" value={data.total_return_pct} precision={2} suffix="%"
              valueStyle={{ color: data.total_return_pct >= 0 ? '#ff4d4d' : '#00d4aa' }} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="最大回撤" value={data.max_drawdown} precision={2} suffix="%" /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="胜率" value={data.win_rate} precision={1} suffix="%" /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="夏普比率" value={data.sharpe_ratio} precision={2} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="交易次数" value={data.total_trades} /></Card></Col>
            <Col xs={12} md={6}><Card size="small"><Statistic title="年化收益" value={(data.annual_return || 0) * 100} precision={2} suffix="%" /></Card></Col>
          </Row>
          {data.trades?.length > 0 && (
            <Card title="交易记录">
              <Table dataSource={data.trades.slice().reverse()} columns={tradeColumns} rowKey="date" pagination={false} size="small" />
            </Card>
          )}
        </>
      )}
    </div>
  );
}
