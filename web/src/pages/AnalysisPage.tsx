import { useState } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Typography, Space, Tag, Alert } from 'antd';
import { ReloadOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Title, Text } = Typography;

export default function AnalysisPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true); setError('');
    try {
      const d = await api.analyze();
      setData(d);
    } catch (e: any) {
      setError(e.message);
    } finally { setLoading(false); }
  };

  const columns = [
    { title: '代码', dataIndex: 'code', key: 'code', width: 100 },
    { title: '名称', dataIndex: 'name', key: 'name', width: 120 },
    { title: '价格', dataIndex: 'price', key: 'price', width: 100, render: (v: number) => v.toFixed(2) },
    {
      title: '涨跌', dataIndex: 'change_pct', key: 'change_pct', width: 90,
      render: (v: number) => (
        <Tag color={v >= 0 ? 'red' : 'green'}>{v >= 0 ? '+' : ''}{v.toFixed(2)}%</Tag>
      ),
    },
    {
      title: '评分', dataIndex: 'score', key: 'score', width: 80,
      render: (v: number) => {
        const color = v >= 70 ? '#00d4aa' : v >= 40 ? '#ffc107' : '#ff4d4d';
        return <span style={{ color, fontWeight: 600 }}>{v.toFixed(0)}</span>;
      },
    },
    { title: '趋势', dataIndex: 'trend', key: 'trend', width: 100 },
    { title: '信号', dataIndex: 'signal', key: 'signal', width: 80 },
    { title: '风险', dataIndex: 'risk', key: 'risk', width: 80 },
    { title: '建议', dataIndex: 'suggestion', key: 'suggestion', width: 100 },
    { title: '支撑', dataIndex: 'support', key: 'support', width: 90, render: (v: number) => v.toFixed(2) },
    { title: '压力', dataIndex: 'resistance', key: 'resistance', width: 90, render: (v: number) => v.toFixed(2) },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={run}>
          执行分析
        </Button>
        {data && <Text type="secondary">完成: {data.count} 只股票</Text>}
      </Space>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} />}

      {data?.summaries && (
        <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
          {Object.entries(data.summaries).map(([code, summary]: any) => {
            const lines = summary.split('\n');
            const nameLine = lines[0] || '';
            const priceLine = lines[1] || '';
            const scoreLine = lines[2] || '';
            const match = nameLine.match(/[🟢🔴⚪🟡]\s*(.*)\((.*)\)/);
            return (
              <Col xs={24} sm={12} md={8} lg={6} key={code}>
                <Card size="small" hoverable>
                  <Statistic
                    title={match ? match[1] : code}
                    value={parseFloat(priceLine.match(/[\d.]+/)?.[0] || '0')}
                    suffix={priceLine.match(/[+-]\d+\.\d+%/)?.[0] || ''}
                    valueStyle={{ color: priceLine.includes('+') ? '#ff4d4d' : '#00d4aa' }}
                  />
                  <div style={{ marginTop: 8, fontSize: 12, color: '#8899aa', whiteSpace: 'pre-wrap' }}>{summary}</div>
                </Card>
              </Col>
            );
          })}
        </Row>
      )}

      {data?.report && (
        <Card title="📄 完整报告">
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7, color: '#e0e0e0' }}>
            {data.report}
          </pre>
        </Card>
      )}
    </div>
  );
}
