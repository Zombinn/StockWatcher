import { useState, useEffect } from 'react';
import { Card, Button, Row, Col, Spin, Tag, Typography, Space, Empty, Divider } from 'antd';
import { ReloadOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

function IndexSection() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.marketReview().then(d => setItems(d.indices || [])).finally(() => setLoading(false));
  }, []);

  if (loading) return <Card className="glass-card" title="📈 主要指数"><Spin /></Card>;
  return (
    <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>📈 主要指数</span>}>
      {items.length > 0 ? items.map((i: any, idx: number) => {
        const isUp = i.change_pct >= 0;
        return (
          <div key={i.name} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 0',
            borderBottom: idx < items.length - 1 ? '1px solid rgba(0,0,0,0.04)' : 'none',
          }}>
            <span style={{ color: '#64748b', fontSize: 14 }}>{i.name}</span>
            <Space size={8}>
              <span style={{ color: '#1a1a2e', fontWeight: 500 }}>{i.price}</span>
              <Tag color={isUp ? 'red' : 'green'} style={{ margin: 0, fontSize: 13, padding: '0 8px', lineHeight: '22px', borderRadius: 4 }}
                icon={isUp ? <RiseOutlined /> : <FallOutlined />}>
                {isUp ? '+' : ''}{i.change_pct}%
              </Tag>
            </Space>
          </div>
        );
      }) : <Empty description="暂无指数数据" />}
    </Card>
  );
}

function NorthboundSection() {
  const [item, setItem] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.marketReview().then(d => setItem(d.northbound || null)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Card className="glass-card" title="🔄 北向资金" style={{ marginTop: 16 }}><Spin /></Card>;
  const isInflow = item?.total_net >= 0;
  return (
    <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>🔄 北向资金</span>} style={{ marginTop: 16 }}>
      {item ? (
        <div style={{ textAlign: 'center', padding: '8px 0' }}>
          <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 4 }}>合计净流入</Text>
          <span style={{
            fontSize: 28, fontWeight: 700,
            color: isInflow ? '#e53935' : '#43a047',
          }}>
            {isInflow ? '+' : ''}{item.total_net}
            <span style={{ fontSize: 14, fontWeight: 400, marginLeft: 4, opacity: 0.5 }}>亿</span>
          </span>
          <Divider style={{ borderColor: 'rgba(0,0,0,0.04)', margin: '12px 0 0' }} />
        </div>
      ) : <Text type="secondary">暂无数据</Text>}
    </Card>
  );
}

function TopSectorsSection() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.marketReview().then(d => setItems(d.top_sectors || [])).finally(() => setLoading(false));
  }, []);

  if (loading) return <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>🟢 领涨板块</span>}><Spin /></Card>;
  return (
    <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>🟢 领涨板块</span>}>
      {items.length > 0 ? items.slice(0, 8).map((s: any, idx: number) => (
        <div key={s.name} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '7px 0',
          borderBottom: idx < Math.min(items.length, 8) - 1 ? '1px solid rgba(0,0,0,0.04)' : 'none',
        }}>
          <span style={{ color: '#64748b', fontSize: 13 }}>{s.name}</span>
          <Tag color="red" style={{ margin: 0, fontSize: 12, borderRadius: 4 }} icon={<RiseOutlined />}>+{s.change_pct}%</Tag>
        </div>
      )) : <Empty description="暂无板块数据" />}
    </Card>
  );
}

function FallSectorsSection() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.marketReview().then(d => setItems(d.fall_sectors || [])).finally(() => setLoading(false));
  }, []);

  if (loading) return <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>🔴 领跌板块</span>} style={{ marginTop: 16 }}><Spin /></Card>;
  return (
    <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>🔴 领跌板块</span>} style={{ marginTop: 16 }}>
      {items.length > 0 ? items.slice(0, 8).map((s: any, idx: number) => (
        <div key={s.name} style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '7px 0',
          borderBottom: idx < Math.min(items.length, 8) - 1 ? '1px solid rgba(0,0,0,0.04)' : 'none',
        }}>
          <span style={{ color: '#64748b', fontSize: 13 }}>{s.name}</span>
          <Tag color="green" style={{ margin: 0, fontSize: 12, borderRadius: 4 }} icon={<FallOutlined />}>{s.change_pct}%</Tag>
        </div>
      )) : <Empty description="暂无板块数据" />}
    </Card>
  );
}

export default function MarketPage() {
  const [key, setKey] = useState(0);

  return (
    <div key={key}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>大盘复盘</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>市场概览与资金流向</Text>
        </div>
        <Button type="primary" icon={<ReloadOutlined />} onClick={() => setKey(k => k + 1)}>刷新复盘</Button>
      </div>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <IndexSection />
          <NorthboundSection />
        </Col>
        <Col xs={24} md={12}>
          <TopSectorsSection />
          <FallSectorsSection />
        </Col>
      </Row>
    </div>
  );
}
