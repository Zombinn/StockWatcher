import { useState } from 'react';
import { Card, Button, Row, Col, Statistic, Spin, Tag, Alert, Typography, Space } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Title, Text } = Typography;

export default function MarketPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true); setError('');
    try {
      const d = await api.marketReview();
      setData(d);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={run}>大盘复盘</Button>
      </Space>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

      {data && (
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card title="📈 主要指数">
              {data.indices?.map((i: any) => (
                <div key={i.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #1e3a5f' }}>
                  <span>{i.name}</span>
                  <span style={{ color: i.change_pct >= 0 ? '#ff4d4d' : '#00d4aa', fontWeight: 600 }}>
                    {i.price} ({i.change_pct >= 0 ? '+' : ''}{i.change_pct}%)
                  </span>
                </div>
              ))}
            </Card>
            <Card title="🔄 北向资金" style={{ marginTop: 16 }}>
              {data.northbound ? (
                <Statistic
                  title="合计净流入"
                  value={data.northbound.total_net}
                  suffix="亿"
                  valueStyle={{ color: data.northbound.total_net >= 0 ? '#ff4d4d' : '#00d4aa' }}
                />
              ) : <Text type="secondary">暂无数据</Text>}
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="🟢 领涨板块">
              {data.top_sectors?.slice(0, 8).map((s: any) => (
                <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #1e3a5f' }}>
                  <span>{s.name}</span> <Tag color="red">+{s.change_pct}%</Tag>
                </div>
              ))}
            </Card>
            <Card title="🔴 领跌板块" style={{ marginTop: 16 }}>
              {data.fall_sectors?.slice(0, 8).map((s: any) => (
                <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #1e3a5f' }}>
                  <span>{s.name}</span> <Tag color="green">{s.change_pct}%</Tag>
                </div>
              ))}
            </Card>
          </Col>
          {data.llm_analysis && (
            <Col span={24}>
              <Card title="🤖 AI 分析">
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{JSON.stringify(data.llm_analysis, null, 2)}</pre>
              </Card>
            </Col>
          )}
        </Row>
      )}
    </div>
  );
}
