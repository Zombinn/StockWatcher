import { useState, useEffect, Component } from 'react';
import { Card, Button, Select, Tag, Typography, Space, Row, Col, Alert, Empty, Table, Drawer, Statistic, message } from 'antd';
import { SearchOutlined, BarChartOutlined, RiseOutlined, FallOutlined, StarOutlined, CheckOutlined, LineChartOutlined } from '@ant-design/icons';
import { api } from '../api';
import ForecastChart from '../components/ForecastChart';

const { Text } = Typography;

class ChartErrorBoundary extends Component<{ children: React.ReactNode }, { err: boolean }> {
  state = { err: false };
  static getDerivedStateFromError() { return { err: true }; }
  render() {
    if (this.state.err)
      return <div style={{ padding: '20px 0', color: '#94a3b8', fontSize: 13, textAlign: 'center' }}>图表加载失败</div>;
    return this.props.children;
  }
}

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

  const [watchlistCodes, setWatchlistCodes] = useState<Set<string>>(new Set());
  const [detailStock, setDetailStock] = useState<any>(null);
  const [addingToWl, setAddingToWl] = useState(false);
  const [selectedCodes, setSelectedCodes] = useState<string[]>([]);
  const [batchAdding, setBatchAdding] = useState(false);

  const loadWatchlist = async () => {
    try {
      const r = await api.getWatchlist();
      setWatchlistCodes(new Set((r.data || []).map((s: any) => s.code as string)));
    } catch {}
  };

  useEffect(() => { loadWatchlist(); }, []);

  const runScreen = async () => {
    setLoading(true); setError(''); setRan(true); setSelectedCodes([]);
    try {
      const d = await api.screenStocks(market, strategy);
      setResults(d.data || []);
    } catch (e: any) {
      setError(e.message || '选股失败');
    } finally {
      setLoading(false);
    }
  };

  const addToWatchlist = async (code: string) => {
    setAddingToWl(true);
    try {
      await api.addWatchlist(code);
      message.success(`已加入自选: ${code}`);
      await loadWatchlist();
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setAddingToWl(false);
    }
  };

  const batchAddToWatchlist = async () => {
    setBatchAdding(true);
    try {
      for (const code of selectedCodes) {
        await api.addWatchlist(code);
      }
      message.success(`已加入自选 ${selectedCodes.length} 支`);
      setSelectedCodes([]);
      await loadWatchlist();
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setBatchAdding(false);
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

  const s = detailStock;
  const isUp = s && (s.change_pct ?? 0) >= 0;
  const scoreColor = s ? (s.score >= 70 ? '#43a047' : s.score >= 40 ? '#f9a825' : '#e53935') : '#64748b';
  const inWatchlist = s && watchlistCodes.has(s.code);

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
          <Select value={market} size="small" style={{ width: 90 }} onChange={v => { setMarket(v); setResults([]); setRan(false); setSelectedCodes([]); }}
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
        <Card className="glass-card"
          title={<span style={{ fontSize: 15, fontWeight: 600 }}>筛选结果</span>}
          extra={selectedCodes.length > 0 && (
            <Space size={8}>
              <Text type="secondary" style={{ fontSize: 13 }}>已选 {selectedCodes.length} 支</Text>
              <Button size="small" type="primary" icon={<StarOutlined />}
                loading={batchAdding} onClick={batchAddToWatchlist}>
                加入自选
              </Button>
              <Button size="small" onClick={() => setSelectedCodes([])}>取消</Button>
            </Space>
          )}
        >
          <Table
            dataSource={results}
            columns={columns}
            rowKey="code"
            pagination={false}
            size="small"
            scroll={{ x: 'max-content' }}
            rowSelection={{
              selectedRowKeys: selectedCodes,
              onChange: (keys) => setSelectedCodes(keys as string[]),
              getCheckboxProps: (record) => ({
                disabled: watchlistCodes.has(record.code),
                title: watchlistCodes.has(record.code) ? '已在自选' : undefined,
              }),
            }}
            onRow={(record) => ({
              style: { cursor: 'pointer' },
              onClick: (e) => {
                // don't open drawer when clicking checkbox
                const target = e.target as HTMLElement;
                if (target.closest('.ant-checkbox-wrapper') || target.closest('.ant-checkbox')) return;
                setDetailStock(record);
              },
            })}
          />
        </Card>
      ) : (
        <Card className="glass-card">
          <Empty description={ran ? '暂无符合条件的标的' : '选择市场和策略，点击「开始筛选」'} />
        </Card>
      )}

      {/* 股票详情抽屉 */}
      <Drawer
        title={
          <Space>
            <LineChartOutlined style={{ color: '#f5642a' }} />
            <span>{s?.name || s?.code}</span>
            <Text type="secondary" style={{ fontSize: 13 }}>{s?.code}</Text>
          </Space>
        }
        placement="right"
        width={540}
        open={!!detailStock}
        onClose={() => setDetailStock(null)}
        styles={{ body: { padding: '16px 20px' } }}
        extra={
          s && (
            <Button
              type={inWatchlist ? 'default' : 'primary'}
              icon={inWatchlist ? <CheckOutlined /> : <StarOutlined />}
              disabled={inWatchlist || addingToWl}
              loading={addingToWl}
              onClick={() => addToWatchlist(s.code)}
            >
              {inWatchlist ? '已在自选' : '加入自选'}
            </Button>
          )
        }
      >
        {s && (
          <>
            {/* 概览数据 */}
            <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Card size="small" className="glass-card" bodyStyle={{ padding: '10px 14px' }}>
                  <Statistic
                    title="现价"
                    value={s.price ?? '--'}
                    precision={2}
                    valueStyle={{ color: isUp ? '#e53935' : '#43a047', fontSize: 20, fontWeight: 600 }}
                    suffix={
                      s.change_pct != null
                        ? <span style={{ fontSize: 13, fontWeight: 500, color: isUp ? '#e53935' : '#43a047' }}>
                            {isUp ? '+' : ''}{s.change_pct?.toFixed(2)}%
                          </span>
                        : undefined
                    }
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" className="glass-card" bodyStyle={{ padding: '10px 14px' }}>
                  <Statistic title="评分" value={s.score?.toFixed(0) ?? '--'}
                    valueStyle={{ color: scoreColor, fontSize: 20, fontWeight: 700 }} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" className="glass-card" bodyStyle={{ padding: '10px 14px' }}>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>信号</div>
                  <Tag style={{
                    fontSize: 14, borderRadius: 4, padding: '2px 10px',
                    color: SIGNAL_COLOR[s.signal] || '#94a3b8',
                    border: `1px solid ${(SIGNAL_COLOR[s.signal] || '#94a3b8')}40`,
                    background: `${(SIGNAL_COLOR[s.signal] || '#94a3b8')}0d`,
                  }}>{s.signal || '--'}</Tag>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" className="glass-card" bodyStyle={{ padding: '10px 14px' }}>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>趋势</div>
                  <Text strong style={{ fontSize: 14 }}>{s.trend || '--'}</Text>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" className="glass-card" bodyStyle={{ padding: '10px 14px' }}>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>风险</div>
                  {s.risk
                    ? <Tag color={s.risk.includes('低') ? '#43a047' : s.risk.includes('中') ? '#f9a825' : '#e53935'}
                        style={{ borderRadius: 4, border: 'none', fontSize: 14, padding: '2px 10px' }}>
                        {s.risk}
                      </Tag>
                    : '--'}
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" className="glass-card" bodyStyle={{ padding: '10px 14px' }}>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>支撑 / 压力</div>
                  <Text style={{ fontSize: 13 }}>
                    <span style={{ color: '#43a047' }}>{s.support?.toFixed(2) ?? '--'}</span>
                    <span style={{ color: '#d0d0d0', margin: '0 4px' }}>/</span>
                    <span style={{ color: '#e53935' }}>{s.resistance?.toFixed(2) ?? '--'}</span>
                  </Text>
                </Card>
              </Col>
            </Row>

            {/* 筛选理由 */}
            {s.reason && (
              <div style={{
                background: 'rgba(245,100,42,0.04)', borderRadius: 8,
                padding: '10px 14px', marginBottom: 20,
                borderLeft: '3px solid rgba(245,100,42,0.25)',
              }}>
                <Text type="secondary" style={{ fontSize: 13 }}>筛选理由：{s.reason}</Text>
              </div>
            )}

            {/* TimesFM 价格预测 */}
            <div style={{ marginBottom: 8 }}>
              <Text strong style={{ fontSize: 14 }}>价格预测</Text>
              <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>基于 TimesFM 时序模型</Text>
            </div>
            <ChartErrorBoundary><ForecastChart code={s.code} name={s.name} /></ChartErrorBoundary>
          </>
        )}
      </Drawer>
    </div>
  );
}
