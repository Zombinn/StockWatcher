import { useState, useEffect, useCallback, useRef } from 'react';
import { Card, Button, Input, Tag, Typography, Space, Row, Col, Spin, Alert, Empty, Divider, message } from 'antd';
import {
  SearchOutlined, RobotOutlined, BarChartOutlined,
  RiseOutlined, FallOutlined, ReloadOutlined, ThunderboltOutlined,
  SafetyOutlined, GlobalOutlined, StarOutlined, CheckOutlined,
} from '@ant-design/icons';
import { api } from '../api';
import { MARKET_OPTIONS } from '../constants';
import { useWatchlist } from '../hooks/useWatchlist';
import { analysisApi, type StockCandidate } from '../api/analysisApi';

const { Text } = Typography;

/* ─────────── 指数面板 ─────────── */
function IndexCards({ data }: { data: any }) {
  const indices: any[] = data?.indices || [];
  if (!indices.length) return null;
  return (
    <Row gutter={[10, 10]}>
      {indices.map((idx: any) => {
        const isUp = (idx.change_pct ?? 0) >= 0;
        return (
          <Col key={idx.name} xs={12} sm={6}>
            <Card className="stat-card" bodyStyle={{ padding: '12px 14px' }}>
              <Text type="secondary" style={{ fontSize: 11 }}>{idx.name}</Text>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#1a1a2e', margin: '2px 0' }}>{idx.price}</div>
              <Tag color={isUp ? 'red' : 'green'} style={{ margin: 0, fontSize: 12, borderRadius: 3 }}
                icon={isUp ? <RiseOutlined /> : <FallOutlined />}>
                {isUp ? '+' : ''}{idx.change_pct}%
              </Tag>
            </Card>
          </Col>
        );
      })}
    </Row>
  );
}

/* ─────────── 北向资金 ─────────── */
function NorthboundCard({ data }: { data: any }) {
  const nb = data?.northbound;
  if (!nb) return null;
  const isInflow = (nb.total_net ?? 0) >= 0;
  return (
    <Card className="glass-card" bodyStyle={{ padding: '14px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <ThunderboltOutlined style={{ color: '#f5642a' }} />
        <Text strong style={{ fontSize: 13 }}>北向资金</Text>
      </div>
      <div style={{ textAlign: 'center' }}>
        <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>合计净流入</Text>
        <span style={{ fontSize: 26, fontWeight: 700, color: isInflow ? '#e53935' : '#43a047' }}>
          {isInflow ? '+' : ''}{nb.total_net}
          <span style={{ fontSize: 12, fontWeight: 400, marginLeft: 3, opacity: 0.5 }}>亿</span>
        </span>
      </div>
    </Card>
  );
}

/* ─────────── 板块排行 ─────────── */
function SectorList({ title, items, icon, up }: { title: string; items: any[]; icon: React.ReactNode; up: boolean }) {
  const isEmpty = !items || items.length === 0;
  return (
    <Card className="glass-card" title={
      <Space size={6}>
        {icon}
        <Text strong style={{ fontSize: 13 }}>{title}</Text>
      </Space>
    } bodyStyle={{ padding: '8px 14px' }}>
      {isEmpty ? (
        <div style={{ textAlign: 'center', padding: '20px 0', color: '#94a3b8', fontSize: 12 }}>
          当前市场无板块数据
        </div>
      ) : items.slice(0, 8).map((s: any, i: number) => (
        <div key={s.name} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '6px 0',
          borderBottom: i < Math.min(items.length, 8) - 1 ? '1px solid rgba(0,0,0,0.04)' : 'none',
        }}>
          <Space size={8}>
            <Text style={{ fontSize: 11, color: '#94a3b8', width: 16 }}>{i + 1}</Text>
            <Text style={{ fontSize: 13, color: '#64748b' }}>{s.name}</Text>
          </Space>
          <Tag color={up ? 'red' : 'green'} style={{ margin: 0, fontSize: 11, borderRadius: 3 }}
            icon={up ? <RiseOutlined /> : <FallOutlined />}>
            {up ? '+' : ''}{s.change_pct}%
          </Tag>
        </div>
      ))}
    </Card>
  );
}

/* ─────────── 分析报告 ─────────── */
function ReportPreview({ result, inWatchlist, onAdd, addingToWl }: {
  result: any; inWatchlist?: boolean; onAdd?: () => void; addingToWl?: boolean;
}) {
  if (!result) return null;
  const isUp = (result.change_pct ?? 0) >= 0;
  return (
    <Card className="glass-card" style={{ marginTop: 20, borderLeft: `3px solid ${isUp ? '#e53935' : '#43a047'}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <Space size={12}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <Text strong style={{ fontSize: 22 }}>{result.code}</Text>
            <Text style={{ fontSize: 14, color: '#64748b' }}>{result.name || ''}</Text>
          </div>
          <Tag style={{ fontSize: 14, padding: '2px 10px', borderRadius: 4 }}
            color={isUp ? 'red' : 'green'}
            icon={isUp ? <RiseOutlined /> : <FallOutlined />}>
            {isUp ? '+' : ''}{result.change_pct?.toFixed(2)}%
          </Tag>
        </Space>
        <Space size={10} align="center">
          <Button
            size="small"
            icon={inWatchlist ? <CheckOutlined /> : <StarOutlined />}
            disabled={inWatchlist}
            loading={addingToWl}
            onClick={onAdd}
            style={inWatchlist ? { color: '#94a3b8', borderColor: '#e2e8f0' } : { color: '#f5642a', borderColor: '#f5642a' }}
          >
            {inWatchlist ? '已在自选' : '加入自选'}
          </Button>
          <div style={{ fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>
            {result.price?.toFixed(2)}
          </div>
        </Space>
      </div>

      <Row gutter={12} style={{ marginBottom: 12 }}>
        <Col span={12}>
          <div style={{ background: 'rgba(245,100,42,0.04)', borderRadius: 8, padding: '10px 12px' }}>
            <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>趋势</Text>
            <Text strong style={{ fontSize: 15, color: result.trend?.includes('多头') ? '#e53935' : '#64748b' }}>
              {result.trend || '--'}
            </Text>
          </div>
        </Col>
        <Col span={12}>
          <div style={{ background: 'rgba(30,136,229,0.04)', borderRadius: 8, padding: '10px 12px' }}>
            <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>信号</Text>
            <Text strong style={{ fontSize: 15, color: result.signal === '买入' ? '#e53935' : '#64748b' }}>
              {result.signal || '--'}
            </Text>
          </div>
        </Col>
      </Row>

      {result.score != null && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>综合评分</Text>
            <Text strong style={{ fontSize: 16, color: result.score >= 60 ? '#f5642a' : '#94a3b8' }}>{result.score}/100</Text>
          </div>
          <div style={{ height: 4, background: '#f0f0f0', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ width: `${result.score}%`, height: '100%', background: 'linear-gradient(90deg, #f5642a, #ff8552)', borderRadius: 2, transition: 'width 0.6s ease' }} />
          </div>
        </div>
      )}

      {result.indicators && (
        <Row gutter={8}>
          <Col span={8}><Text type="secondary" style={{ fontSize: 11 }}>MA5</Text><div style={{ fontSize: 13, fontWeight: 500 }}>{result.indicators.ma5?.toFixed(2)}</div></Col>
          <Col span={8}><Text type="secondary" style={{ fontSize: 11 }}>MA10</Text><div style={{ fontSize: 13, fontWeight: 500 }}>{result.indicators.ma10?.toFixed(2)}</div></Col>
          <Col span={8}><Text type="secondary" style={{ fontSize: 11 }}>MA20</Text><div style={{ fontSize: 13, fontWeight: 500 }}>{result.indicators.ma20?.toFixed(2)}</div></Col>
          <Col span={8} style={{ marginTop: 6 }}><Text type="secondary" style={{ fontSize: 11 }}>RSI14</Text><div style={{ fontSize: 13, fontWeight: 500 }}>{result.indicators.rsi_14?.toFixed(1)}</div></Col>
          <Col span={8} style={{ marginTop: 6 }}><Text type="secondary" style={{ fontSize: 11 }}>MACD</Text><div style={{ fontSize: 13, fontWeight: 500 }}>{result.indicators.macd_hist?.toFixed(3)}</div></Col>
          <Col span={8} style={{ marginTop: 6 }}><Text type="secondary" style={{ fontSize: 11 }}>乖离率</Text><div style={{ fontSize: 13, fontWeight: 500 }}>{result.indicators.bias_5?.toFixed(2)}%</div></Col>
        </Row>
      )}
    </Card>
  );
}

/* ─────────── 狙击点位 ─────────── */
function StrategyPoints({ result }: { result: any }) {
  if (!result) return null;
  return (
    <Card className="glass-card" title={<Text strong style={{ fontSize: 13 }}>🎯 狙击点位</Text>}
      bodyStyle={{ padding: '12px 14px' }} style={{ marginTop: 12 }}>
      <Row gutter={8}>
        <Col span={6}>
          <div style={{ background: 'rgba(245,100,42,0.06)', borderRadius: 6, padding: '8px 10px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 10 }}>支撑位</Text>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#f5642a' }}>{result.support?.toFixed(2) || '--'}</div>
          </div>
        </Col>
        <Col span={6}>
          <div style={{ background: 'rgba(30,136,229,0.06)', borderRadius: 6, padding: '8px 10px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 10 }}>理想买点</Text>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#1e88e5' }}>
              {(result.support + (result.price - result.support) * 0.3)?.toFixed(2) || '--'}
            </div>
          </div>
        </Col>
        <Col span={6}>
          <div style={{ background: 'rgba(249,168,37,0.06)', borderRadius: 6, padding: '8px 10px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 10 }}>压力位</Text>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#f9a825' }}>{result.resistance?.toFixed(2) || '--'}</div>
          </div>
        </Col>
        <Col span={6}>
          <div style={{ background: 'rgba(67,160,71,0.06)', borderRadius: 6, padding: '8px 10px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: 10 }}>止盈参考</Text>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#43a047' }}>{(result.resistance * 1.05)?.toFixed(2) || '--'}</div>
          </div>
        </Col>
      </Row>
    </Card>
  );
}

/* ─────────── 主页面 ─────────── */
export default function HomePage() {
  const [query, setQuery] = useState('');
  const [market, setMarket] = useState('cn');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [marketData, setMarketData] = useState<any>(null);
  const [marketLoading, setMarketLoading] = useState(true);
  const [suggestions, setSuggestions] = useState<StockCandidate[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [recommend, setRecommend] = useState<StockCandidate[]>([]);
  const [symbols, setSymbols] = useState<StockCandidate[]>([]);
  const { watchlistCodes, loadWatchlist } = useWatchlist();
  const [addingToWl, setAddingToWl] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMarketLoading(true);
    api.marketReview(market)
      .then(d => setMarketData(d))
      .catch(() => {})
      .finally(() => setMarketLoading(false));
  }, [market]);

  useEffect(() => { loadWatchlist(); }, []);

  // Load recommendations when market changes
  useEffect(() => {
    analysisApi.searchRecommend(market).then(setRecommend).catch(() => {});
  }, [market]);

  // 页面打开时加载「自选 + 持仓」去重代码，供输入框下拉
  useEffect(() => {
    api.getSymbols()
      .then(d => setSymbols((d.data || []).map((s: any) => ({ code: s.code, name: s.name, market: s.market }))))
      .catch(() => {});
  }, []);

  // Search suggest（空查询展示自选+持仓；输入时先本地筛选自选+持仓，再并入全市场搜索结果）
  useEffect(() => {
    const q = query.trim().toUpperCase();
    if (q.length >= 1) {
      const localMatches = symbols.filter(
        s => s.code.toUpperCase().includes(q) || (s.name || '').toUpperCase().includes(q)
      );
      setSuggestions(localMatches);   // 立即按输入筛选自选+持仓
      setShowDropdown(true);
      analysisApi.searchSuggest(query, market).then(remote => {
        const seen = new Set(localMatches.map(s => s.code));
        setSuggestions([...localMatches, ...remote.filter(r => !seen.has(r.code))]);
      }).catch(() => {});
    } else {
      setSuggestions(symbols);
    }
  }, [query, market, symbols]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSearch = useCallback(async (code?: string) => {
    const target = (code || query || '').trim().toUpperCase();
    if (!target) { setError('请输入股票代码'); return; }
    setAnalyzing(true);
    setError('');
    setResult(null);
    setShowDropdown(false);
    try {
      const res = await api.analyzeStock(target);
      setResult(res.data || res);
    } catch (e: any) {
      setError(e.message || '分析失败');
    } finally {
      setAnalyzing(false);
    }
  }, [query]);

  const selectCandidate = (item: StockCandidate) => {
    setQuery(item.code);
    setShowDropdown(false);
    handleSearch(item.code);
  };

  const addToWatchlist = async () => {
    if (!result?.code) return;
    setAddingToWl(true);
    try {
      await api.addWatchlist(result.code);
      await loadWatchlist();
      message.success(`${result.code} 已加入自选`);
    } catch (e: any) {
      message.error(e.message || '加入自选失败');
    } finally {
      setAddingToWl(false);
    }
  };

  return (
    <div style={{ maxWidth: "100%" }}>
      {/* Title */}
      <div style={{ marginBottom: 16 }}>
        <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>StockWatcher 智能分析</Text>
        <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>
          多市场股票技术分析 + AI 解读
        </Text>
      </div>

      {/* Market selector + Search */}
      <Card className="glass-card" bodyStyle={{ padding: '14px 16px' }} style={{ marginBottom: 16 }}>
        <Space direction="vertical" size={10} style={{ width: '100%' }}>
          {/* Market selector row */}
          <Space size={8}>
            <GlobalOutlined style={{ color: '#94a3b8' }} />
            {MARKET_OPTIONS.map(m => (
              <Tag key={m.value}
                style={{
                  cursor: 'pointer', fontSize: 13, padding: '3px 12px', borderRadius: 6,
                  transition: 'all 0.2s',
                  background: market === m.value ? 'rgba(245,100,42,0.08)' : undefined,
                  border: market === m.value ? '1px solid rgba(245,100,42,0.3)' : undefined,
                  color: market === m.value ? '#f5642a' : undefined,
                  fontWeight: market === m.value ? 600 : undefined,
                }}
                onClick={() => setMarket(m.value)}>
                {m.label}
              </Tag>
            ))}
          </Space>

          {/* Search with dropdown */}
          <div ref={searchRef} style={{ position: 'relative' }}>
            <Space.Compact style={{ width: '100%' }}>
              <Input
                size="large"
                placeholder="输入股票代码或名称搜索..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                onPressEnter={() => handleSearch()}
                prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
                style={{ borderRadius: '8px 0 0 8px' }}
                onFocus={() => { if (suggestions.length) setShowDropdown(true); }}
              />
              <Button type="primary" size="large" icon={<RobotOutlined />}
                loading={analyzing} onClick={() => handleSearch()}
                style={{ borderRadius: '0 8px 8px 0', paddingLeft: 20, paddingRight: 20 }}>
                分析
              </Button>
            </Space.Compact>

            {/* Suggest dropdown */}
            {showDropdown && suggestions.length > 0 && (
              <div style={{
                position: 'absolute', top: '100%', left: 0, right: 0,
                background: '#fff', borderRadius: 8, boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
                zIndex: 100, marginTop: 4, maxHeight: 400, overflow: 'auto',
                border: '1px solid rgba(0,0,0,0.06)',
              }}>
                {suggestions.map(s => (
                  <div key={s.code} onClick={() => selectCandidate(s)}
                    style={{
                      padding: '10px 14px', cursor: 'pointer', display: 'flex',
                      justifyContent: 'space-between', alignItems: 'center',
                      borderBottom: '1px solid rgba(0,0,0,0.04)',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#fff5f0')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                    <Space size={10}>
                      <Text strong style={{ fontSize: 14 }}>{s.code}</Text>
                      <Text style={{ fontSize: 13, color: '#64748b' }}>{s.name}</Text>
                    </Space>
                    <Tag style={{ fontSize: 10, borderRadius: 3, margin: 0 }}>
                      {s.market.toUpperCase()}
                    </Tag>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recommendations */}
          {!query && recommend.length > 0 && (
            <div>
              <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>推荐热门股票</Text>
              <Space size={6} wrap>
                {recommend.map(s => (
                  <Tag key={s.code} style={{ cursor: 'pointer', fontSize: 12, borderRadius: 4, padding: '2px 10px' }}
                    onClick={() => selectCandidate(s)}>
                    {s.name} <Text style={{ fontSize: 10, opacity: 0.6 }}>({s.code})</Text>
                  </Tag>
                ))}
              </Space>
            </div>
          )}
        </Space>
      </Card>

      {error && <Alert type="error" message={error} showIcon closable onClose={() => setError('')} style={{ marginBottom: 16 }} />}

      {analyzing && (
        <Card className="glass-card" bodyStyle={{ padding: 60 }}>
          <div style={{ textAlign: 'center' }}>
            <div className="loading-breathe" style={{ marginBottom: 16 }}>
              <div className="dot-pulse" style={{ margin: '0 auto' }} />
            </div>
            <Text className="loading-text" style={{ fontSize: 13 }}>AI 分析中...</Text>
          </div>
        </Card>
      )}

      {result && !analyzing && (
        <>
          <ReportPreview result={result} inWatchlist={watchlistCodes.has(result.code)} onAdd={addToWatchlist} addingToWl={addingToWl} />
          <StrategyPoints result={result} />
          {result.suggestion && (
            <Card className="glass-card" bodyStyle={{ padding: '12px 16px' }} style={{ marginTop: 12 }}>
              <Space size={8}>
                <SafetyOutlined style={{ color: result.suggestion?.includes('买入') ? '#e53935' : '#94a3b8' }} />
                <Text style={{ fontSize: 14 }}>操作建议：</Text>
                <Text strong style={{ fontSize: 14, color: result.suggestion?.includes('买入') ? '#e53935' : '#64748b' }}>
                  {result.suggestion}
                </Text>
              </Space>
            </Card>
          )}
        </>
      )}

      <Divider style={{ borderColor: 'rgba(0,0,0,0.04)', margin: '24px 0' }} />

      {/* Market Review */}
      <div style={{ marginBottom: 12 }}>
        <Space size={8}>
          <BarChartOutlined style={{ color: '#f5642a', fontSize: 16 }} />
          <Text strong style={{ fontSize: 16, color: '#1a1a2e' }}>大盘概览</Text>
        </Space>
        <Button type="text" size="small" icon={<ReloadOutlined />}
          onClick={() => { setMarketLoading(true); api.marketReview(market).then(d => setMarketData(d)).finally(() => setMarketLoading(false)); }}
          style={{ float: 'right', color: '#94a3b8' }} />
      </div>

      {marketLoading ? (
        <Card className="glass-card" bodyStyle={{ padding: 40 }}>
          <Space><Spin size="small" /><Text type="secondary" style={{ fontSize: 12 }}>加载 {MARKET_OPTIONS.find(m => m.value === market)?.label || market} 数据...</Text></Space>
        </Card>
      ) : marketData ? (
        <>
          <IndexCards data={marketData} />
          <div style={{ display: 'flex', gap: 12, marginTop: 12, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 300 }}>
              <SectorList title="领涨板块" items={marketData.top_sectors || []} icon={<RiseOutlined style={{ color: '#e53935' }} />} up />
            </div>
            <div style={{ flex: 1, minWidth: 300 }}>
              <SectorList title="领跌板块" items={marketData.fall_sectors || []} icon={<FallOutlined style={{ color: '#43a047' }} />} up={false} />
            </div>
          </div>
        </>
      ) : (
        <Card className="glass-card"><Empty description={`${MARKET_OPTIONS.find(m => m.value === market)?.label || market} 暂无市场数据`} /></Card>
      )}
    </div>
  );
}
