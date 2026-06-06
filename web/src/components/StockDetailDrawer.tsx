import React, { useState } from 'react';
import { Drawer, Card, Row, Col, Statistic, Tag, Typography, Button, Space, message, Spin } from 'antd';
import {
  LineChartOutlined, StarOutlined, CheckOutlined,
  RiseOutlined, FallOutlined,
} from '@ant-design/icons';
import { api } from '../api';
import KLineChart from './KLineChart';
import ForecastChart from './ForecastChart';

const { Text } = Typography;

const SIGNAL_COLOR: Record<string, string> = {
  '强烈买入': '#e53935', '买入': '#f5642a', '持有': '#1e88e5',
  '观望': '#94a3b8', '卖出': '#43a047', '强烈卖出': '#2e7d32',
};

interface Props {
  stock: any;
  inWatchlist: boolean;
  onClose: () => void;
  onAddToWatchlist?: (code: string) => void;
}

export default function StockDetailDrawer({ stock, inWatchlist, onClose, onAddToWatchlist }: Props) {
  const s = stock;
  const isUp = s && (s.change_pct ?? 0) >= 0;
  const scoreColor = s ? (s.score >= 70 ? '#43a047' : s.score >= 40 ? '#f9a825' : '#e53935') : '#64748b';

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
      width={600}
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
            <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>近 60 个交易日</Text>
          </div>
          <KLineChart code={s.code} name={s.name} />

          {/* TimesFM 价格预测 */}
          <div style={{ marginTop: 16, marginBottom: 8 }}>
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
