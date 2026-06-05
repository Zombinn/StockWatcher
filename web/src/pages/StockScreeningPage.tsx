import { useState } from 'react';
import { Card, Button, Select, Tag, Typography, Space, Row, Col, Alert, Empty, Table } from 'antd';
import { SearchOutlined, BarChartOutlined, RiseOutlined, FallOutlined, StarOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

const MARKET_STRATEGIES: Record<string, { id: string; name: string; desc: string }[]> = {
  cn: [
    { id: 'top_gainers',       name: '强势突破', desc: '涨幅最大的标的' },
    { id: 'oversold_reversal', name: '超跌反弹', desc: 'RSI 偏低、乖离率大，关注反弹' },
    { id: 'blue_chip',         name: '综合评分', desc: '按技术评分排序' },
  ],
  hk: [
    { id: 'top_gainers', name: '强势突破', desc: '港股涨幅领先标的' },
    { id: 'blue_chip',   name: '蓝筹精选', desc: '港股综合评分排序' },
  ],
  us: [
    { id: 'top_gainers', name: '强势突破', desc: '美股涨幅领先标的' },
    { id: 'blue_chip',   name: '蓝筹精选', desc: '美股综合评分排序' },
    { id: 'growth',      name: '成长精选', desc: '按评分筛选潜力股' },
  ],
};

const SIGNAL_COLOR: Record<string, string> = {
  买入: '#e53935', 强烈买入: '#f5642a', 持有: '#1e88e5', 观望: '#94a3b8', 卖出: '#43a047',
};

function StrategyCard({ s, active, onSelect }: { s: { id: string; name: string; desc: string }; active: boolean; onSelect: () => void }) {
  return (
    <Card hoverable className="glass-card" onClick={onSelect} bodyStyle={{ padding: '12px 14px' }}
      style={{ cursor: 'pointer', border: active ? '1px solid rgba(245,100,42,0.4)' : undefined, background: active ? 'rgba(245,100,42,0.03)' : undefined }}>
      <Space direction="vertical" size={3} style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          <BarChartOutlined style={{ color: active ? '#f5642a' : '#94a3b8' }} />
          <Text strong style={{ color: active ? '#f5642a' : '#1a1a2e', fontSize: 14 }}>{s.name}</Text>
        </div>
        <Text type="secondary" style={{ fontSize: 12 }}>{s.desc}</Text>
      </Space>
    </Card>
  );
}

export default function StockScreeningPage() {
  const [market, setMarket] = useState('cn');
  const [strategy, setStrategy] = useState('top_gainers');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ran, setRan] = useState(false);

  const runScreen = async () => {
    setLoading(true); setError(''); setRan(true);
    try {
      const d = await api.screenStocks(market, strategy);
      setResults(d.data || []);
    } catch (e: any) {
      setError(e.message || '选股失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '排名', width: 50, render: (_: any, __: any, idx: number) => (
        <span style={{ fontWeight: 600, color: idx < 3 ? '#f5642a' : '#94a3b8', fontSize: 14 }}>{idx + 1}</span>
      )
    },
    { title: '代码', dataIndex: 'code', width: 90 },
    { title: '名称', dataIndex: 'name', width: 120 },
    { title: '现价', dataIndex: 'price', width: 85, align: 'right' as const,
      render: (v: number) => v ? <span style={{ fontWeight: 500 }}>{v.toFixed(2)}</span> : '--' },
    { title: '涨跌', dataIndex: 'change_pct', width: 90,
      render: (v: number) => v != null
        ? <Tag color={v >= 0 ? 'red' : 'green'} icon={v >= 0 ? <RiseOutlined /> : <FallOutlined />} style={{ borderRadius: 4 }}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}%
          </Tag>
        : '--',
      sorter: (a: any, b: any) => (a.change_pct ?? 0) - (b.change_pct ?? 0),
    },
    { title: '评分', dataIndex: 'score', width: 65,
      render: (v: number) => {
        const c = v >= 70 ? '#43a047' : v >= 40 ? '#f9a825' : '#e53935';
        return <span style={{ color: c, fontWeight: 700 }}>{v?.toFixed(0)}</span>;
      },
      sorter: (a: any, b: any) => (a.score ?? 0) - (b.score ?? 0),
    },
    { title: '趋势', dataIndex: 'trend', width: 80 },
    { title: '信号', dataIndex: 'signal', width: 70,
      render: (v: string) => {
        const c = SIGNAL_COLOR[v] || '#94a3b8';
        return <Tag style={{ borderRadius: 4, color: c, border: `1px solid ${c}40`, background: `${c}0d`, margin: 0 }}>{v}</Tag>;
      },
    },
    { title: '风险', dataIndex: 'risk', width: 80,
      render: (v: string) => {
        if (!v) return '-';
        const c = v.includes('低') ? '#43a047' : v.includes('中') ? '#f9a825' : '#e53935';
        return <Tag color={c} style={{ borderRadius: 4, border: 'none', margin: 0 }}>{v}</Tag>;
      },
    },
    { title: '支撑', dataIndex: 'support', width: 80, align: 'right' as const,
      render: (v: number) => v?.toFixed(2) ?? '--' },
    { title: '压力', dataIndex: 'resistance', width: 80, align: 'right' as const,
      render: (v: number) => v?.toFixed(2) ?? '--' },
    { title: '筛选理由', dataIndex: 'reason', ellipsis: true },
  ];

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>智能选股</Text>
        <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>
          实时行情 + 技术分析，筛选候选标的
        </Text>
      </div>

      <Row gutter={[10, 10]} style={{ marginBottom: 14 }}>
        {(MARKET_STRATEGIES[market] || MARKET_STRATEGIES['cn']).map(s => (
          <Col key={s.id} xs={12} sm={8} md={6}>
            <StrategyCard s={s} active={strategy === s.id} onSelect={() => setStrategy(s.id)} />
          </Col>
        ))}
      </Row>

      <Card className="glass-card" bodyStyle={{ padding: '12px 16px' }} style={{ marginBottom: 16 }}>
        <Space wrap size={12}>
          <Select value={market} size="small" style={{ width: 90 }} onChange={v => { setMarket(v); setResults([]); setRan(false); }}
            options={[
              { value: 'cn', label: '🇨🇳 A股' },
              { value: 'hk', label: '🇭🇰 港股' },
              { value: 'us', label: '🇺🇸 美股' },
            ]} />
          <Button type="primary" icon={<SearchOutlined />} loading={loading} onClick={runScreen} size="small">
            开始筛选
          </Button>
          {results.length > 0 && <Text type="secondary" style={{ fontSize: 12 }}>共 {results.length} 个候选（实时分析结果）</Text>}
        </Space>
      </Card>

      {error && <Alert type="error" message={error} showIcon closable onClose={() => setError('')} style={{ marginBottom: 16 }} />}

      {loading ? (
        <Card className="glass-card" bodyStyle={{ padding: 80 }}>
          <div style={{ textAlign: 'center' }}>
            <div className="loading-breathe" style={{ marginBottom: 16 }}>
              <div className="dot-pulse" style={{ margin: '0 auto' }} />
            </div>
            <Text className="loading-text" style={{ fontSize: 13 }}>正在拉取行情 + 技术分析中…</Text>
          </div>
        </Card>
      ) : results.length > 0 ? (
        <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>筛选结果</span>}>
          <Table dataSource={results} columns={columns} rowKey="code"
            pagination={false} size="small" scroll={{ x: 'max-content' }} />
        </Card>
      ) : (
        <Card className="glass-card">
          <Empty description={ran ? '暂无符合条件的标的' : '选择市场和策略，点击「开始筛选」'} />
        </Card>
      )}
    </div>
  );
}
