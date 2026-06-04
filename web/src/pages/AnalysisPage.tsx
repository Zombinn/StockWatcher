import { useState, useEffect } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Tag, Alert, Typography, Space, Spin, Empty } from 'antd';
import { ReloadOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

export default function AnalysisPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true); setError('');
    try { const d = await api.analyze(); setData(d); }
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
    { title: '风险', dataIndex: 'risk', key: 'risk', width: 70,
      render: (v: string) => {
        if (!v) return '-';
        const color = v === '低' ? '#43a047' : v === '中' ? '#f9a825' : '#e53935';
        return <Tag color={color} style={{ border: 'none', borderRadius: 4 }}>{v}</Tag>;
      },
    },
    { title: '建议', dataIndex: 'suggestion', key: 'suggestion', width: 100 },
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
          <Text className="loading-text" style={{ fontSize: 13 }}>正在分析中...</Text>
        </div>
      ) : data ? (
        <>
          {data.summaries && (
            <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
              {Object.entries(data.summaries).map(([code, summary]: any, idx: number) => {
                const lines = summary.split('\n');
                const nameLine = lines[0] || '';
                const priceLine = lines[1] || '';
                const match = nameLine.match(/[🟢🔴⚪🟡]\s*(.*)\((.*)\)/);
                const priceMatch = priceLine.match(/[\d.]+/);
                const changeMatch = priceLine.match(/[+-]\d+\.\d+%/);
                const isUp = priceLine.includes('+');
                return (
                  <Col xs={24} sm={12} md={8} lg={6} key={code} className={`fade-in fade-in-delay-${idx % 5}`}>
                    <Card className="glass-card" size="small" hoverable>
                      <Statistic
                        title={<span style={{ color: '#64748b' }}>{match ? match[1] : code}</span>}
                        value={priceMatch ? parseFloat(priceMatch[0]) : 0}
                        suffix={changeMatch
                          ? <span style={{ fontSize: 14, fontWeight: 500, color: isUp ? '#e53935' : '#43a047' }}>{changeMatch[0]}</span>
                          : ''}
                        valueStyle={{ color: isUp ? '#e53935' : '#43a047', fontWeight: 600, fontSize: 22 }}
                      />
                      <div style={{ marginTop: 8, fontSize: 12, color: '#94a3b8', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{summary}</div>
                    </Card>
                  </Col>
                );
              })}
            </Row>
          )}
          {data.report && (
            <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>📄 完整报告</span>}>
              <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7, color: '#475569', fontFamily: 'inherit' }}>{data.report}</pre>
            </Card>
          )}
        </>
      ) : (
        <Card className="glass-card"><Text type="secondary">暂无数据，请点击"刷新分析"</Text></Card>
      )}
    </div>
  );
}
