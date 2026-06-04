import { useState } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Tag, Alert, Select, Space, Typography, Empty } from 'antd';
import { ExperimentOutlined, ReloadOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { api } from '../api';
import SymbolSelect from '../components/SymbolSelect';

const { Text } = Typography;

const strategies = [
  { value: 'ma_cross', label: '均线金叉' },
  { value: 'macd', label: 'MACD' },
  { value: 'rsi', label: 'RSI' },
  { value: 'bollinger', label: '布林带' },
];

export default function BacktestPage() {
  const [code, setCode] = useState('');
  const [strategy, setStrategy] = useState('ma_cross');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const run = async (autoCode?: string) => {
    const c = autoCode || code;
    if (!c) { setError('请输入或选择股票代码'); return; }
    setLoading(true); setError('');
    try { const d = await api.backtest(c, strategy); setData(d.data); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const tradeColumns = [
    { title: '日期', dataIndex: 'date', width: 105,
      render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: '#64748b' }}>{v}</span>,
    },
    { title: '操作', dataIndex: 'action', width: 65,
      render: (v: string) => <Tag color={v === 'buy' ? 'red' : 'green'} style={{ borderRadius: 4 }}>{v === 'buy' ? '买入' : '卖出'}</Tag>,
    },
    { title: '价格', dataIndex: 'price', width: 85, align: 'right' as const,
      render: (v: number) => v?.toFixed(2) ?? '-',
    },
    { title: '数量', dataIndex: 'shares', width: 70, align: 'right' as const },
    { title: '金额', dataIndex: 'amount', width: 95, align: 'right' as const,
      render: (v: number) => v?.toFixed(2) ?? '-',
    },
    { title: '理由', dataIndex: 'reason' },
  ];

  const isPositive = (data?.total_return_pct ?? 0) >= 0;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>策略回测</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>历史数据验证交易策略</Text>
        </div>
      </div>
      <Card className="glass-card" style={{ marginBottom: 20 }}>
        <Space wrap>
          <SymbolSelect value={code} onChange={setCode} style={{ width: 200 }} />
          <Select value={strategy} onChange={v => { setStrategy(v); }} options={strategies} style={{ width: 130 }} />
          <Button type="primary" icon={<ExperimentOutlined />} loading={loading} onClick={() => run()}>回测</Button>
        </Space>
      </Card>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <div className="loading-breathe" style={{ marginBottom: 16 }}>
            <div className="dot-pulse" style={{ margin: '0 auto' }} />
          </div>
          <Text className="loading-text" style={{ fontSize: 13 }}>正在回测中...</Text>
        </div>
      ) : data ? (
        <>
          <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
            {[
              { title: '初始资金', value: data.initial_capital, unit: '', color: undefined },
              { title: '最终价值', value: data.final_value, unit: '', color: isPositive ? '#e53935' : '#43a047' },
              { title: '总收益', value: data.total_return_pct, unit: '%', color: isPositive ? '#e53935' : '#43a047', prefix: isPositive ? <RiseOutlined /> : <FallOutlined /> },
              { title: '最大回撤', value: data.max_drawdown, unit: '%', color: undefined },
              { title: '胜率', value: data.win_rate, unit: '%', color: undefined },
              { title: '夏普比率', value: data.sharpe_ratio, unit: '', color: undefined },
              { title: '交易次数', value: data.total_trades, unit: '', color: undefined },
              { title: '年化收益', value: (data.annual_return || 0) * 100, unit: '%', color: isPositive ? '#e53935' : '#43a047', prefix: isPositive ? <RiseOutlined /> : <FallOutlined /> },
            ].map((s, i) => (
              <Col xs={12} sm={6} key={i}>
                <Card className="stat-card" size="small">
                  <Statistic
                    title={<span style={{ color: '#64748b' }}>{s.title}</span>}
                    value={s.value}
                    precision={s.title === '交易次数' ? 0 : 2}
                    suffix={s.unit ? <span style={{ fontSize: 14, color: '#94a3b8' }}>{s.unit}</span> : ''}
                    prefix={s.prefix}
                    valueStyle={{ color: s.color ?? '#1a1a2e', fontWeight: 600, fontSize: 20 }}
                  />
                </Card>
              </Col>
            ))}
          </Row>
          <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>交易记录</span>}>
            {data.trades?.length > 0 ? (
              <Table dataSource={data.trades.slice().reverse()} columns={tradeColumns} rowKey="date" pagination={false} size="small" />
            ) : <Empty description="该策略未产生交易" />}
          </Card>
        </>
      ) : (
        <Card className="glass-card"><Text type="secondary">输入股票代码点击"回测"开始</Text></Card>
      )}
    </div>
  );
}
