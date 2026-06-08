import React, { useState, useEffect } from 'react';
import { Drawer, Card, Row, Col, Statistic, Tag, Typography, Button, Space, message, Spin, Empty, Popover } from 'antd';
import {
  LineChartOutlined, StarOutlined, CheckOutlined,
} from '@ant-design/icons';
import { api } from '../api';
import KLineChart from './KLineChart';
import ForecastChart from './ForecastChart';

const { Text } = Typography;

const SIGNAL_COLOR: Record<string, string> = {
  '强烈买入': '#e53935', '买入': '#f5642a', '持有': '#1e88e5',
  '观望': '#94a3b8', '卖出': '#43a047', '强烈卖出': '#2e7d32',
};

const DIRECTION_COLOR: Record<string, string> = {
  bullish: '#e53935',
  bearish: '#43a047',
  neutral: '#94a3b8',
};

interface Props {
  stock: any;
  inWatchlist: boolean;
  onClose: () => void;
  onAddToWatchlist?: (code: string) => void;
}

const PATTERN_EXPLANATIONS: Record<string, string> = {
  '头肩顶': '价格三次冲高，中间最高（头部），两边较低（肩膀），是见顶反转信号。跌破颈线（两肩低点连线）意味着上涨趋势可能结束。',
  '头肩底': '价格三次探底，中间最低（头部），两边较高（肩膀），是见底反转信号。突破颈线（两肩高点连线）意味着下跌趋势可能反转。',
  '双顶': '价格两次冲高到相近高点后回落，像字母 M，是见顶反转信号。跌破中间低点意味着上涨可能结束。',
  '双底': '价格两次探底到相近低点后反弹，像字母 W，是见底反转信号。突破中间高点意味着下跌可能反转。',
  '对称三角形': '价格波动幅度逐渐收窄，高点降低、低点抬高，形成对称三角。整理形态，突破方向决定后续走势。',
  '上升三角形': '高点基本水平，低点不断抬高，买方力量增强，向上突破概率大，是看涨信号。',
  '下降三角形': '低点基本水平，高点不断降低，卖方力量增强，向下突破概率大，是看跌信号。',
  '上升旗形': '急涨后在小幅下降通道中整理，短暂整理后大概率继续上涨，可在旗形下沿关注。',
  '下降旗形': '急跌后在小幅上升通道中整理，短暂整理后大概率继续下跌，持仓者可考虑反弹减仓。',
  '上升楔形': '价格在两条向上收敛的趋势线内运行，上涨动能衰竭，实际是看跌反转信号。',
  '下降楔形': '价格在两条向下收敛的趋势线内运行，下跌动能衰竭，实际是看涨反转信号。',
};

export default function StockDetailDrawer({ stock, inWatchlist, onClose, onAddToWatchlist }: Props) {
  const s = stock;
  const isUp = s && (s.change_pct ?? 0) >= 0;
  const scoreColor = s ? (s.score >= 70 ? '#43a047' : s.score >= 40 ? '#f9a825' : '#e53935') : '#64748b';

  // --- 形态识别 ---
  const [patterns, setPatterns] = useState<any[]>([]);
  const [patternsLoading, setPatternsLoading] = useState(false);

  useEffect(() => {
    if (!s?.code) return;
    setPatternsLoading(true);
    api.stockPatterns(s.code)
      .then(d => setPatterns(d.patterns || []))
      .catch(() => {})
      .finally(() => setPatternsLoading(false));
  }, [s?.code]);

  // --- 财报日历 ---
  const [earnings, setEarnings] = useState<any[]>([]);
  const [earningsLoading, setEarningsLoading] = useState(false);

  useEffect(() => {
    if (!s?.code) return;
    setEarningsLoading(true);
    api.stockEarnings(s.code)
      .then(d => setEarnings(d.earnings || []))
      .catch(() => {})
      .finally(() => setEarningsLoading(false));
  }, [s?.code]);

  return (
    <Drawer
      title={
        <Space>
          <LineChartOutlined style={{ color: '#f5642a' }} />
          <span>{s?.name || s?.code}</span>
          <Text type="secondary" style={{ fontSize: 13 }}>{s?.code}</Text>
        </Space>
      }
      placement="right"
      width={900}
      open={!!s}
      onClose={onClose}
      styles={{ body: { padding: '16px 20px', overflow: 'auto' } }}
      extra={
        s && onAddToWatchlist ? (
          <Button
            type={inWatchlist ? 'default' : 'primary'}
            icon={inWatchlist ? <CheckOutlined /> : <StarOutlined />}
            disabled={inWatchlist}
            onClick={() => onAddToWatchlist(s.code)}
          >
            {inWatchlist ? '已在自选' : '加入自选'}
          </Button>
        ) : null
      }
    >
      {s && s.loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0' }}>
          <Spin />
          <Text type="secondary" style={{ display: 'block', marginTop: 12 }}>加载分析数据中...</Text>
        </div>
      ) : s && (
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
              <Text type="secondary" style={{ fontSize: 13 }}>说明：{s.reason}</Text>
            </div>
          )}

          {/* K 线图 + 成交量 */}
          <div style={{ marginBottom: 8 }}>
            <Text strong style={{ fontSize: 14 }}>K 线图</Text>
          </div>
          <KLineChart code={s.code} name={s.name} />

          {/* 形态识别 */}
          <div style={{ marginTop: 20, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Text strong style={{ fontSize: 14 }}>形态识别</Text>
            <Popover
              title={<span style={{ fontSize: 14, fontWeight: 600 }}>常见形态说明</span>}
              content={
                <div style={{ maxWidth: 300, fontSize: 12.5, lineHeight: 1.8, color: '#475569' }}>
                  {Object.entries(PATTERN_EXPLANATIONS).map(([name, desc]) => (
                    <div key={name} style={{ marginBottom: 8 }}>
                      <strong>{name}</strong>：{desc}
                    </div>
                  ))}
                </div>
              }
              trigger="click"
              placement="bottom"
            >
              <span style={{ cursor: 'pointer', color: '#94a3b8', fontSize: 15, lineHeight: 1 }}>ⓘ</span>
            </Popover>
          </div>
                    {patternsLoading ? (
            <div style={{ textAlign: 'center', padding: 20 }}><Spin size="small" /></div>
          ) : patterns.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {patterns.map((p: any, i: number) => {
                const dirEmoji = p.direction === 'bullish' ? '🟢' : p.direction === 'bearish' ? '🔴' : '⚪';
                const label = PATTERN_EXPLANATIONS[p.name] || '';
                return (
                  <Tag
                    key={i}
                    style={{ padding: '3px 10px', fontSize: 13, borderRadius: 6, cursor: 'default' }}
                    color={p.direction === 'bullish' ? 'red' : p.direction === 'bearish' ? 'green' : 'default'}
                  >
                    {dirEmoji} {p.name}
                    <span style={{ marginLeft: 4, opacity: 0.7, fontSize: 11 }}>
                      {(p.confidence * 100).toFixed(0)}%
                    </span>

                  </Tag>
                );
              })}
            </div>
          ) : (
            <Text type="secondary" style={{ fontSize: 13 }}>未识别到明显形态</Text>
          )}

          {/* 财报日历 */}
          <div style={{ marginTop: 20, marginBottom: 8 }}>
            <Text strong style={{ fontSize: 14 }}>财报日历</Text>
          </div>
          {earningsLoading ? (
            <div style={{ textAlign: 'center', padding: 20 }}><Spin size="small" /></div>
          ) : earnings.length > 0 ? (
            <div style={{ position: 'relative', paddingLeft: 20 }}>
              {/* 时间线竖线 */}
              <div style={{
                position: 'absolute', left: 7, top: 4, bottom: 4, width: 2,
                background: 'rgba(0,0,0,0.08)', borderRadius: 1,
              }} />
              {earnings.map((e: any, i: number) => (
                <div key={e.quarter} style={{ position: 'relative', paddingBottom: 12, paddingLeft: 20 }}>
                  {/* 时间线圆点 */}
                  <div style={{
                    position: 'absolute', left: -13, top: 4, width: 10, height: 10,
                    borderRadius: '50%', background: i === 0 ? '#f5642a' : '#d0d0d0',
                    border: '2px solid #fff', boxShadow: '0 0 0 2px rgba(0,0,0,0.06)',
                  }} />
                  <div style={{
                    background: i === 0 ? 'rgba(245,100,42,0.04)' : '#fafafa',
                    borderRadius: 8, padding: '8px 12px',
                    border: i === 0 ? '1px solid rgba(245,100,42,0.15)' : '1px solid rgba(0,0,0,0.06)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong style={{ fontSize: 13 }}>{e.quarter}</Text>
                      <Tag style={{ fontSize: 11 }}>{e.date}</Tag>
                    </div>
                    <div style={{ display: 'flex', gap: 16, marginTop: 4, fontSize: 12 }}>
                      <span>
                        <span style={{ fontWeight: 500 }}>{e.actual_eps != null ? e.actual_eps.toFixed(4) : '--'}</span>
                      </span>
                      <span>
                        <Text type="secondary">实际 EPS：</Text>
                        <span style={{ fontWeight: 500 }}>{e.actual_eps != null ? e.actual_eps.toFixed(4) : '--'}</span>
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Text type="secondary" style={{ fontSize: 13 }}>暂无财报数据</Text>
          )}

          {/* TimesFM 价格预测 */}
          <div style={{ marginTop: 20, marginBottom: 8 }}>
            <Text strong style={{ fontSize: 14 }}>价格预测</Text>
            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>基于 TimesFM 时序模型</Text>
          </div>
          <ChartErrorBoundary><ForecastChart code={s.code} name={s.name} /></ChartErrorBoundary>
        </>
      )}
    </Drawer>
  );
}

class ChartErrorBoundary extends React.Component<{ children: React.ReactNode }, { err: boolean }> {
  state = { err: false };
  static getDerivedStateFromError() { return { err: true }; }
  render() {
    if (this.state.err) return <Text type="secondary" style={{ fontSize: 12 }}>图表渲染异常，可刷新重试</Text>;
    return this.props.children;
  }
}
