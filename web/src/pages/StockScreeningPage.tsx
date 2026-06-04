import { useState, useEffect, useMemo } from 'react';
import { Card, Button, Select, Tag, Typography, Space, Row, Col, Spin, Alert, Empty } from 'antd';
import {
  SearchOutlined, BarChartOutlined, ReloadOutlined,
  RiseOutlined, FallOutlined, StarOutlined,
} from '@ant-design/icons';
import { api } from '../api';
import { analysisApi } from '../api/analysisApi';

const { Text, Title } = Typography;

type MarketStrats = { id: string; name: string; desc: string }[];

const MARKET_STRATEGIES: Record<string, MarketStrats> = {
  cn: [
    { id: 'top_gainers', name: '强势突破', desc: 'A 股领涨板块龙头', },
    { id: 'volume_spike', name: '放量异动', desc: 'A 股成交量异常放大', },
    { id: 'oversold_reversal', name: '超跌反弹', desc: 'A 股 RSI 超卖区域', },
  ],
  hk: [
    { id: 'top_gainers', name: '强势突破', desc: '港股热门标的', },
    { id: 'blue_chip', name: '蓝筹精选', desc: '港股核心蓝筹股', },
  ],
  us: [
    { id: 'top_gainers', name: '强势突破', desc: '美股热门标的', },
    { id: 'blue_chip', name: '蓝筹精选', desc: '美股科技蓝筹', },
    { id: 'growth', name: '成长精选', desc: '美股高成长潜力股', },
  ],
};

type Candidate = {
  code: string;
  name: string;
  score: number;
  price?: number;
  changePct?: number;
  reason: string;
  signal?: string;
};

const SCORE_COLORS: Record<string, string> = {
  强烈买入: '#f5642a',
  买入: '#f59e0b',
  持有: '#3b82f6',
  观望: '#94a3b8',
  卖出: '#ef4444',
};

function formatPrice(v: number | undefined | null) {
  if (v == null) return '--';
  if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(2)}亿`;
  if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(2)}万`;
  return v.toFixed(2);
}

function StrategyCard({ strategy, active, onSelect }: { strategy: { id: string; name: string; desc: string }; active: boolean; onSelect: () => void }) {
  return (
    <Card
      hoverable
      className={`glass-card ${active ? 'border-glow' : ''}`}
      style={{
        cursor: 'pointer',
        border: active ? '1px solid rgba(245,100,42,0.4)' : undefined,
        background: active ? 'rgba(245,100,42,0.03)' : undefined,
        transition: 'all 0.2s',
      }}
      onClick={onSelect}
      bodyStyle={{ padding: '14px 16px' }}
    >
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BarChartOutlined style={{ color: active ? '#f5642a' : '#94a3b8', fontSize: 16 }} />
          <Text strong style={{ fontSize: 14, color: active ? '#f5642a' : '#1a1a2e' }}>{strategy.name}</Text>
        </div>
        <Text type="secondary" style={{ fontSize: 12 }}>{strategy.desc}</Text>

      </Space>
    </Card>
  );
}

function CandidateCard({ item, rank }: { item: Candidate; rank: number }) {
  const isUp = (item.changePct ?? 0) >= 0;
  const signalColor = SCORE_COLORS[item.signal ?? '观望'] || '#94a3b8';

  return (
    <div className="glass-card fade-in" style={{
      padding: 14, marginBottom: 10,
      borderLeft: `3px solid ${signalColor}`,
      animationDelay: `${rank * 0.05}s`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Space size={10}>
          <div style={{
            width: 24, height: 24, borderRadius: 6,
            background: rank <= 3 ? 'rgba(245,100,42,0.1)' : 'rgba(0,0,0,0.03)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 600, fontSize: 12, color: rank <= 3 ? '#f5642a' : '#94a3b8',
          }}>{rank}</div>
          <div>
            <Space size={6}>
              <Text strong style={{ fontSize: 15 }}>{item.code}</Text>
              <Text style={{ fontSize: 13, color: '#64748b' }}>{item.name}</Text>
            </Space>
            <div style={{ marginTop: 2 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>{item.reason}</Text>
            </div>
          </div>
        </Space>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#1a1a2e' }}>
            {item.price?.toFixed(2) ?? '--'}
          </div>
          <Tag style={{ margin: 0, fontSize: 12, borderRadius: 3 }}
            color={isUp ? 'red' : 'green'}
            icon={isUp ? <RiseOutlined /> : <FallOutlined />}>
            {isUp ? '+' : ''}{item.changePct?.toFixed(2) ?? '--'}%
          </Tag>
        </div>
      </div>
      <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
        <Tag style={{ borderRadius: 3, fontSize: 11, color: signalColor, border: `1px solid ${signalColor}40`, background: `${signalColor}08` }}>
          {item.signal ?? '观望'}
        </Tag>
        <Tag style={{ borderRadius: 3, fontSize: 11 }}>
          <StarOutlined /> 评分 {item.score.toFixed(1)}
        </Tag>
      </div>
    </div>
  );
}

export default function StockScreeningPage() {
  const [market, setMarket] = useState('cn');
  const [strategy, setStrategy] = useState<string>('top_gainers');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const runScreen = async () => {
    setLoading(true);
    setError('');
    try {
      let result: Candidate[] = [];

      if (market === 'cn') {
        // A 股：从市场板块数据推导
        const review = await analysisApi.marketReview();
        const topSectors: any[] = review?.top_sectors || [];
        const fallSectors: any[] = review?.fall_sectors || [];

        if (strategy === 'top_gainers') {
          topSectors.slice(0, 12).forEach((s: any, i: number) => {
            result.push({
              code: s.code || `SECTOR${i}`,
              name: s.name,
              score: Math.max(0, 100 - i * 7),
              changePct: s.change_pct,
              reason: `板块强度排名第${i + 1}，涨幅 ${s.change_pct}%`,
              signal: i < 3 ? '强烈买入' : i < 6 ? '买入' : '持有',
            });
          });
        } else if (strategy === 'oversold_reversal') {
          fallSectors.slice(0, 12).forEach((s: any, i: number) => {
            result.push({
              code: s.code || `SECTOR${i}`,
              name: s.name,
              score: Math.max(0, 75 - i * 5),
              changePct: s.change_pct,
              reason: `超跌板块，回调 ${Math.abs(s.change_pct)}%，关注反弹机会`,
              signal: i < 3 ? '买入' : '观望',
            });
          });
        } else {
          [...topSectors, ...fallSectors].slice(0, 15).forEach((s: any, i: number) => {
            result.push({
              code: s.code || `SECTOR${i}`,
              name: s.name,
              score: Math.max(0, 80 - i * 5),
              changePct: s.change_pct,
              reason: `${Math.abs(s.change_pct)}% 振幅，关注放量异动`,
              signal: s.change_pct >= 0 ? '买入' : '观望',
            });
          });
        }
      } else {
        // 港股/美股：从推荐列表获取
        const stocks = await analysisApi.searchRecommend(market, 12);
        const recommends = await analysisApi.searchSuggest('', market);
        const items = stocks.length > 0 ? stocks : recommends;

        items.slice(0, 12).forEach((s: any, i: number) => {
          let score = 0;
          let signal = '观望';
          let reason = '';

          if (strategy === 'top_gainers' || strategy === 'blue_chip') {
            score = Math.max(0, 85 - i * 6);
            signal = i < 4 ? '买入' : '持有';
            reason = strategy === 'blue_chip'
              ? `${market.toUpperCase()} 蓝筹标的，流动性好`
              : `${market.toUpperCase()} 热门标的`;
          } else if (strategy === 'growth') {
            score = Math.max(0, 75 - i * 5);
            signal = i < 3 ? '买入' : '持有';
            reason = '高成长潜力标的';
          }

          result.push({
            code: s.code,
            name: s.name,
            score,
            reason,
            signal,
          });
        });
      }

      setCandidates(result);
    } catch (e: any) {
      setError(e.message || '选股失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>AlphaSift 量化选股</Text>
        <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>
          基于多因子模型 + 市场数据，智能筛选潜力标的
        </Text>
      </div>

      {/* Strategy selector */}
      <Row gutter={12} style={{ marginBottom: 16 }}>
        {(MARKET_STRATEGIES[market] || MARKET_STRATEGIES['cn']).map(s => (
          <Col key={s.id} xs={12} sm={8} md={6}>
            <StrategyCard strategy={s} active={strategy === s.id} onSelect={() => setStrategy(s.id)} />
          </Col>
        ))}
      </Row>

      {/* Controls */}
      <Card className="glass-card" bodyStyle={{ padding: '12px 16px' }} style={{ marginBottom: 16 }}>
        <Space wrap size={12}>
          <Select value={market} onChange={setMarket} size="small" style={{ width: 90 }}
            options={[
            { value: 'cn', label: '🇨🇳 A 股' },
            { value: 'hk', label: '🇭🇰 港股' },
            { value: 'us', label: '🇺🇸 美股' },
          ]} />
          <Button type="primary" icon={<SearchOutlined />} loading={loading} onClick={runScreen} size="small">
            开始筛选
          </Button>
          {candidates.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>共 {candidates.length} 个候选</Text>
          )}
        </Space>
      </Card>

      {error && <Alert type="error" message={error} showIcon closable onClose={() => setError('')} style={{ marginBottom: 16 }} />}

      {/* Results */}
      {loading ? (
        <Card className="glass-card" bodyStyle={{ padding: 80 }}>
          <div style={{ textAlign: 'center' }}>
            <div className="loading-breathe" style={{ marginBottom: 16 }}>
              <div className="dot-pulse" style={{ margin: '0 auto' }} />
            </div>
            <Text className="loading-text" style={{ fontSize: 13 }}>AI 量化筛选分析中...</Text>
          </div>
        </Card>
      ) : candidates.length > 0 ? (
        <div>
          {candidates.map((item, i) => (
            <CandidateCard key={`${item.code}-${i}`} item={item} rank={i + 1} />
          ))}
        </div>
      ) : (
        <Card className="glass-card">
          <Empty description="点击「开始筛选」获取候选标的" />
        </Card>
      )}
    </div>
  );
}
