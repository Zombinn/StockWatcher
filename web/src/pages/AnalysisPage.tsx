import { useState, useEffect } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Tag, Alert, Typography, Space, Empty, message } from 'antd';
import { ReloadOutlined, RiseOutlined, FallOutlined, LineChartOutlined } from '@ant-design/icons';
import { api } from '../api';
import { useWatchlist } from '../hooks/useWatchlist';
import StockDetailDrawer from '../components/StockDetailDrawer';

const { Text } = Typography;

export default function AnalysisPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [forecastStock, setForecastStock] = useState<any>(null);
  const { watchlistCodes, loadWatchlist } = useWatchlist();

  useEffect(() => { loadWatchlist(); }, []);

  const load = async () => {
    setLoading(true); setError('');
    try {
      // 分析是后台任务；若服务端返回 loading:true 则轮询直到完成
      let d = await api.analyze();
      while (d.loading) {
        await new Promise(r => setTimeout(r, 8000));
        d = await api.analyze();
      }
      setData(d);
    }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const columns = [
    { title: '代码', dataIndex: 'code', key: 'code', width: 90 },
    { title: '名称', dataIndex: 'name', key: 'name', width: 110 },
    { title: '价格', dataIndex: 'price', key: 'price', width: 90,
      render: (v: number) => v != null ? <span style={{ fontWeight: 500, color: '#1a1a2e' }}>{v.toFixed(2)}</span> : '-' },
    {
      title: '涨跌', dataIndex: 'change_pct', key: 'change_pct', width: 90,
      render: (v: number) => v != null
        ? <Tag color={v >= 0 ? 'red' : 'green'} icon={v >= 0 ? <RiseOutlined /> : <FallOutlined />} style={{ borderRadius: 4 }}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}%
          </Tag>
        : '-',
    },
    {
      title: '评分', dataIndex: 'score', key: 'score', width: 70,
      sorter: (a: any, b: any) => (a.score ?? 0) - (b.score ?? 0),
      render: (v: number) => {
        if (v == null) return '-';
        const color = v >= 70 ? '#43a047' : v >= 40 ? '#f9a825' : '#e53935';
        return <span style={{ color, fontWeight: 700, fontSize: 15 }}>{v.toFixed(0)}</span>;
      },
    },
    { title: '趋势', dataIndex: 'trend', key: 'trend', width: 80 },
    { title: '信号', dataIndex: 'signal', key: 'signal', width: 70 },
    { title: '风险', dataIndex: 'risk', key: 'risk', width: 80,
      render: (v: string) => {
        if (!v) return '-';
        const color = v.includes('低') ? '#43a047' : v.includes('中') ? '#f9a825' : '#e53935';
        return <Tag color={color} style={{ border: 'none', borderRadius: 4 }}>{v}</Tag>;
      },
    },
    { title: '建议', dataIndex: 'suggestion', key: 'suggestion', width: 100,
      render: (v: string) => {
        if (!v) return '-';
        const color = v.includes('买') ? '#e53935' : v.includes('卖') ? '#43a047' : '#64748b';
        return <span style={{ color, fontWeight: 500 }}>{v}</span>;
      },
    },
    { title: '支撑', dataIndex: 'support', key: 'support', width: 80, render: (v: number) => v?.toFixed(2) ?? '-' },
    { title: '压力', dataIndex: 'resistance', key: 'resistance', width: 80, render: (v: number) => v?.toFixed(2) ?? '-' },
  ];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>技术分析</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>多维度扫描与评分</Text>
        </div>
        <Space>
          {data && <Text type="secondary" style={{ fontSize: 13 }}>完成: {data.count} 只股票</Text>}
          <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={load}>刷新分析</Button>
        </Space>
      </div>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <div className="loading-breathe" style={{ marginBottom: 16 }}>
            <div className="dot-pulse" style={{ margin: '0 auto' }} />
          </div>
          <Text className="loading-text" style={{ fontSize: 13 }}>后台分析中（首次约需 1-2 分钟）…</Text>
        </div>
      ) : data && data.stocks?.length ? (
        <>
          {/* 概览卡片 */}
          <div style={{ maxHeight: 380, overflowY: 'auto', marginBottom: 16, paddingRight: 4 }}>
          <Row gutter={[12, 12]}>
            {data.stocks.map((s: any, idx: number) => {
              const isUp = (s.change_pct ?? 0) >= 0;
              const scoreColor = s.score >= 70 ? '#43a047' : s.score >= 40 ? '#f9a825' : '#e53935';
              return (
                <Col xs={24} sm={12} md={8} lg={6} key={s.code} className={`fade-in fade-in-delay-${idx % 5}`}>
                  <Card className="glass-card" size="small" hoverable
                    onClick={() => setForecastStock(s)}>
                    <Statistic
                      title={<span style={{ color: '#64748b' }}>{s.name || s.code} <Text type="secondary" style={{ fontSize: 11 }}>{s.code}</Text></span>}
                      value={s.price ?? 0}
                      precision={2}
                      suffix={<span style={{ fontSize: 14, fontWeight: 500, color: isUp ? '#e53935' : '#43a047' }}>
                        {isUp ? '+' : ''}{s.change_pct?.toFixed(2)}%
                      </span>}
                      valueStyle={{ color: isUp ? '#e53935' : '#43a047', fontWeight: 600, fontSize: 22 }}
                    />
                    <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Space size={6}>
                        <Tag color="default" style={{ borderRadius: 4, margin: 0 }}>{s.trend}</Tag>
                        <Tag color={s.signal?.includes('买') ? 'red' : s.signal?.includes('卖') ? 'green' : 'default'}
                          style={{ borderRadius: 4, margin: 0 }}>{s.signal}</Tag>
                      </Space>
                      <Space size={6}>
                        <span style={{ color: scoreColor, fontWeight: 700, fontSize: 18 }}>{s.score?.toFixed(0)}</span>
                        <LineChartOutlined style={{ color: '#f5642a', opacity: 0.6, fontSize: 14 }} title="点击查看预测" />
                      </Space>
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>
          </div>

          {/* 明细表 */}
          <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>分析明细</span>}>
            <Table dataSource={data.stocks} columns={columns} rowKey="code" pagination={{ defaultPageSize: 10, pageSizeOptions: [10, 20, 50], showSizeChanger: true }} size="small"
              scroll={{ x: 'max-content' }} />
          </Card>
        </>
      ) : data ? (
        <Card className="glass-card"><Empty description="无分析结果（请检查自选股配置）" /></Card>
      ) : (
        <Card className="glass-card"><Text type="secondary">暂无数据，请点击"刷新分析"</Text></Card>
      )}

      <StockDetailDrawer
        stock={forecastStock}
        inWatchlist={!!(forecastStock && watchlistCodes.has(forecastStock.code))}
        onClose={() => setForecastStock(null)}
        onAddToWatchlist={async (code: string) => {
          try {
            const r = await api.addWatchlist(code);
            if (r.added) { message.success('已加入自选'); loadWatchlist(); }
          } catch (e: any) { message.error(e.message); }
        }}
      />
    </div>
  );
}
