import { useState, useEffect } from 'react';
import {
  Card, Button, Row, Col, Spin, Tag, Alert, Typography, Space, Empty, Segmented, Tooltip, Modal,
} from 'antd';
import { ReloadOutlined, CalendarOutlined, AppstoreOutlined, InfoCircleOutlined, RiseOutlined, FallOutlined, LineChartOutlined } from '@ant-design/icons';
import { api } from '../api';
import { MARKET_OPTIONS } from '../constants';

const { Text } = Typography;

// ====== 指数 ======
function IndexSection({ indices }: { indices: any[] }) {
  return (
    <Card className="glass-card" title={<><LineChartOutlined style={{ marginRight: 6 }} />主要指数</>}>
      {indices.length > 0 ? indices.map((i: any) => (
        <div key={i.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
          <span>{i.name}</span>
          <span style={{ color: i.change_pct >= 0 ? '#e53935' : '#43a047', fontWeight: 600 }}>
            {i.price} ({i.change_pct >= 0 ? '+' : ''}{i.change_pct}%)
          </span>
        </div>
      )) : <Empty description="暂无指数数据" />}
    </Card>
  );
}

// ====== 领涨板块 ======
function TopSectorsSection({ items }: { items: any[] }) {
  return (
    <Card className="glass-card" title={<><RiseOutlined style={{ marginRight: 6 }} />领涨板块</>}>
      {items.length > 0 ? items.slice(0, 10).map((s: any) => (
        <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
          <span>{s.name}</span> <Tag color="red">+{s.change_pct}%</Tag>
        </div>
      )) : <Empty description="暂无板块数据" />}
    </Card>
  );
}

// ====== 领跌板块 ======
function FallSectorsSection({ items }: { items: any[] }) {
  return (
    <Card className="glass-card" title={<><FallOutlined style={{ marginRight: 6 }} />领跌板块</>}>
      {items.length > 0 ? items.slice(0, 10).map((s: any) => (
        <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
          <span>{s.name}</span> <Tag color="green">{s.change_pct}%</Tag>
        </div>
      )) : <Empty description="暂无板块数据" />}
    </Card>
  );
}

// ====== 板块热力图 ======
function SectorTreemap({ items }: { items: any[] }) {
  if (items.length === 0) return <Card title={<><AppstoreOutlined style={{ marginRight: 6 }} />板块热力图</>}><Empty description="暂无数据" /></Card>;

  const sorted = [...items].sort((a, b) => Math.abs(b.change_pct) - Math.abs(a.change_pct)).slice(0, 30);
  const maxAbs = Math.max(...sorted.map(s => Math.abs(s.change_pct)), 0.1);
  const cols = 5;

  return (
    <Card title={<><AppstoreOutlined style={{ marginRight: 6 }} />板块热力图</>}>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 6, maxHeight: 320, overflowY: 'auto' }}>
        {sorted.map((s: any) => {
          const pct = s.change_pct;
          const isUp = pct >= 0;
          const intensity = Math.min(Math.abs(pct) / maxAbs, 1);
          const bWidth = Math.round(2 + 3 * intensity);
          const borderC = isUp ? '#fca5a5' : '#86efac';
          const textColor = intensity > 0.4 ? (isUp ? '#dc2626' : '#16a34a') : '#94a3b8';
          return (
            <Tooltip key={s.name} title={`${s.name}: ${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`}>
              <div style={{
                border: `${bWidth}px solid ${borderC}`,
                background: '#fff',
                color: textColor, borderRadius: 8, padding: '8px 6px',
                textAlign: 'center', cursor: 'pointer', minHeight: 50,
                display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
                transition: 'transform 0.15s',
              }}
                onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05)'}
                onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
              >
                <span style={{ fontSize: 11, fontWeight: 600, lineHeight: 1.3, color: '#0f172a' }}>{s.name}</span>
                <span style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>
                  {pct >= 0 ? '+' : ''}{pct.toFixed(2)}%
                </span>
              </div>
            </Tooltip>
          );
        })}
      </div>
    </Card>
  );
}

// ====== 经济日历 ======
function EconomicCalendar() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<any | null>(null);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    api.economicCalendar(90).then(d => setEvents(d.events || [])).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const impColor: Record<string, string> = { high: '#e53935', medium: '#f9a825', low: '#94a3b8' };
  const impLabel: Record<string, string> = { high: '高', medium: '中', low: '低' };
  const today = new Date().toISOString().slice(0, 10);
  const filtered = filter === 'all' ? events : events.filter(e => e.importance === filter);
  const upcoming = filtered.filter(e => e.date >= today).slice(0, 10);
  const past = filtered.filter(e => e.date < today).slice(0, 5);

  if (loading) return <Card title={<><CalendarOutlined style={{ marginRight: 6 }} />经济日历</>}><Spin /></Card>;

  return (
    <Card
      title={<><CalendarOutlined style={{ marginRight: 6 }} />经济日历</>}
      extra={
        <Segmented value={filter} onChange={(v) => setFilter(v as string)}
          options={[
            { label: '全部', value: 'all' },
            { label: '高', value: 'high' },
            { label: '中', value: 'medium' },
            { label: '低', value: 'low' },
          ]}
          size="small"
        />
      }
    >
      {events.length === 0 ? <Empty description="暂无经济日历数据" /> : (
        <>
          {upcoming.length > 0 && (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1a1a2e', marginBottom: 8 }}>即将发布 ({upcoming.length})</div>
              {upcoming.map((e: any, i: number) => (
                <div key={`up-${i}`} onClick={() => setDetail(e)} style={{
                  display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
                  padding: '6px 0', borderBottom: '1px solid rgba(0,0,0,0.04)',
                }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: impColor[e.importance] || '#94a3b8', flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: '#1a1a2e', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.title}</div>
                    <div style={{ fontSize: 11, color: '#94a3b8' }}>{e.country} · {e.date}</div>
                  </div>
                  <Tag style={{ fontSize: 10, lineHeight: '16px', margin: 0, flexShrink: 0 }} color={impColor[e.importance]}>{impLabel[e.importance]}</Tag>
                </div>
              ))}
            </>
          )}
          {past.length > 0 && upcoming.length > 0 && <div style={{ height: 1, background: 'rgba(0,0,0,0.06)', margin: '8px 0' }} />}
          {past.length > 0 && (
            <>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1a1a2e', marginBottom: 8, marginTop: 4 }}>历史事件</div>
              {past.map((e: any, i: number) => (
                <div key={`past-${i}`} onClick={() => setDetail(e)} style={{
                  display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer',
                  padding: '6px 0', borderBottom: '1px solid rgba(0,0,0,0.04)', opacity: 0.7,
                }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: impColor[e.importance] || '#94a3b8', flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 500, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.title}</div>
                    <div style={{ fontSize: 11, color: '#94a3b8' }}>{e.country} · {e.date}{e.actual ? ` · 实际: ${e.actual}` : ''}</div>
                  </div>
                  <Tag style={{ fontSize: 10, lineHeight: '16px', margin: 0, flexShrink: 0 }} color={impColor[e.importance]}>{impLabel[e.importance]}</Tag>
                </div>
              ))}
            </>
          )}
        </>
      )}

      <Modal
        title={<span><InfoCircleOutlined style={{ marginRight: 8, color: '#f5642a' }} />{detail?.title || '事件详情'}</span>}
        open={!!detail}
        onCancel={() => setDetail(null)}
        footer={null}
        width={420}
      >
        {detail && (
          <div style={{ padding: '8px 0' }}>
            <div style={{ marginBottom: 12, display: 'flex', gap: 24 }}>
              <div><div style={{ fontSize: 12, color: '#94a3b8' }}>国家</div><div style={{ fontWeight: 500, marginTop: 2 }}>{detail.country}</div></div>
              <div><div style={{ fontSize: 12, color: '#94a3b8' }}>日期</div><div style={{ fontWeight: 500, marginTop: 2 }}>{detail.date}</div></div>
              <div>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>重要性</div>
                <div style={{ marginTop: 2 }}>
                  <Tag color={detail.importance === 'high' ? 'red' : detail.importance === 'medium' ? 'orange' : 'default'}>
                    {detail.importance === 'high' ? '高' : detail.importance === 'medium' ? '中' : '低'}
                  </Tag>
                </div>
              </div>
            </div>
            {detail.indicator && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 12, color: '#94a3b8' }}>指标</div>
                <div style={{ fontWeight: 500, marginTop: 2 }}>{detail.indicator}</div>
              </div>
            )}
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              {detail.previous != null && detail.previous !== '' && (
                <div><div style={{ fontSize: 12, color: '#94a3b8' }}>前值</div><div style={{ fontWeight: 600, marginTop: 2 }}>{detail.previous}</div></div>
              )}
              {detail.forecast != null && detail.forecast !== '' && (
                <div><div style={{ fontSize: 12, color: '#94a3b8' }}>预测值</div><div style={{ fontWeight: 600, marginTop: 2, color: '#f9a825' }}>{detail.forecast}</div></div>
              )}
              {detail.actual != null && detail.actual !== '' && (
                <div><div style={{ fontSize: 12, color: '#94a3b8' }}>实际值</div><div style={{ fontWeight: 600, marginTop: 2, color: '#e53935' }}>{detail.actual}</div></div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </Card>
  );
}

// ====== 主页面 ======

export default function MarketPage() {
  const [tab, setTab] = useState('overview');
  const [market, setMarket] = useState('cn');
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true); setError('');
    api.marketReview(market)
      .then(d => setMarketData(d))
      .catch(() => setError('大盘数据加载失败'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [market]);

  const indices = marketData?.indices || [];
  const topSectors = marketData?.top_sectors || [];
  const fallSectors = marketData?.fall_sectors || [];
  const allSectors = marketData?.all_sectors || [];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Space>
          {MARKET_OPTIONS.map(m => (
            <Tag key={m.value}
              style={{
                cursor: 'pointer', fontSize: 13, padding: '3px 12px', borderRadius: 6,
                transition: 'all 0.2s',
                background: market === m.value ? 'rgba(245,100,42,0.08)' : undefined,
                border: market === m.value ? '1px solid rgba(245,100,42,0.3)' : '1px solid transparent',
                color: market === m.value ? '#f5642a' : undefined,
                fontWeight: market === m.value ? 600 : undefined,
              }}
              onClick={() => setMarket(m.value)}>
              {m.label}
            </Tag>
          ))}
        </Space>
        <Segmented
          value={tab}
          onChange={(v) => setTab(v as string)}
          options={[
            { label: '大盘概览', value: 'overview' },
            { label: '经济日历', value: 'calendar' },
          ]}
        />
        <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={load}>刷新</Button>
      </div>

      {error && <Alert type="error" message={error} showIcon closable onClose={() => setError('')} style={{ marginBottom: 16 }} />}

      {tab === 'overview' && (
        loading ? (
          <Card className="glass-card" bodyStyle={{ padding: 60, textAlign: 'center' }}><Spin /></Card>
        ) : (
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Row gutter={16}>
                <Col xs={24} md={8}><IndexSection indices={indices} /></Col>
                <Col xs={24} md={8}><TopSectorsSection items={topSectors} /></Col>
                <Col xs={24} md={8}><FallSectorsSection items={fallSectors} /></Col>
              </Row>
            </Col>
            <Col span={24}>
              <SectorTreemap items={allSectors} />
            </Col>
          </Row>
        )
      )}

      {tab === 'calendar' && <EconomicCalendar />}
    </div>
  );
}
