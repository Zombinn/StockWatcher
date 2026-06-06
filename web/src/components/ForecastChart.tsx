import { useState, useEffect } from 'react';
import { Card, Button, Select, Spin, Typography, Tag, Alert } from 'antd';
import { Line } from '@ant-design/charts';
import { RobotOutlined, ReloadOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

interface Props {
  code: string;
  name?: string;
}

export default function ForecastChart({ code, name }: Props) {
  const [horizon, setHorizon] = useState(14);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);  // 默认 true，避免白屏
  const [error, setError] = useState('');

  const load = async (h = horizon) => {
    if (!code) return;
    setLoading(true); setError('');
    try {
      const d = await api.stockForecast(code, h);
      setData(d);
    } catch (e: any) {
      setError(e.message || '预测失败（模型加载中，稍后重试）');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [code]);

  // Build chart data: historical anchor point + forecast with bands
  const chartData = data ? [
    // anchor: last known price
    {
      date: data.last_date, value: data.last_price,
      lower90: data.last_price, upper90: data.last_price,
      lower80: data.last_price, upper80: data.last_price,
      type: 'actual',
    },
    // forecast points
    ...data.dates.map((date: string, i: number) => ({
      date,
      value: data.forecast[i],
      lower90: data.lower_90[i],
      upper90: data.upper_90[i],
      lower80: data.lower_80[i],
      upper80: data.upper_80[i],
      type: 'forecast',
    })),
  ] : [];

  // Trend from last price to final forecast
  const trendPct = data
    ? ((data.forecast[data.forecast.length - 1] - data.last_price) / data.last_price * 100)
    : null;

  const yMin = chartData.length > 0 ? Math.min(...chartData.map((d: any) => d.value)) * 0.98 : undefined;
  const yMax = chartData.length > 0 ? Math.max(...chartData.map((d: any) => d.value)) * 1.02 : undefined;

  const config = {
    data: chartData,
    xField: 'date',
    yField: 'value',
    smooth: true,
    animation: { appear: { animation: 'path-in', duration: 600 } },
    point: { style: { r: 2, fill: '#f5642a' }, state: { selected: { r: 4 } } },
    style: { stroke: '#f5642a', lineWidth: 2 },
    axis: {
      x: { label: { style: { fontSize: 11, fill: '#94a3b8' } }, title: false },
      y: { label: { style: { fontSize: 11, fill: '#94a3b8' } }, title: false },
    },
    tooltip: {
      items: [
        { channel: 'y', name: '预测价', valueFormatter: (v: number) => v?.toFixed(2) },
      ],
    },
    scale: { y: { domain: [yMin!, yMax!] } },
  };

  return (
    <Card
      className="glass-card"
      style={{ marginTop: 12 }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ color: '#f5642a' }} />
          <span style={{ fontSize: 15, fontWeight: 600 }}>TimesFM 价格预测</span>
          <Tag style={{ borderRadius: 4, fontSize: 11, margin: 0 }}>google/timesfm-1.0-200m</Tag>
          {trendPct !== null && (
            <Tag color={trendPct >= 0 ? 'red' : 'green'} style={{ borderRadius: 4, margin: 0 }}>
              {horizon}日预期 {trendPct >= 0 ? '+' : ''}{trendPct.toFixed(2)}%
            </Tag>
          )}
        </div>
      }
      extra={
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Select
            size="small"
            value={horizon}
            style={{ width: 90 }}
            options={[
              { value: 7,  label: '7天' },
              { value: 14, label: '14天' },
              { value: 30, label: '30天' },
            ]}
            onChange={v => { setHorizon(v); load(v); }}
          />
          <Button size="small" icon={<ReloadOutlined />} onClick={() => load()} loading={loading} />
        </div>
      }
    >
      {error && (
        <Alert type="warning" message={error} showIcon closable
          onClose={() => setError('')} style={{ marginBottom: 12 }} />
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="default" />
          <Text type="secondary" style={{ display: 'block', marginTop: 12, fontSize: 13 }}>
            {data ? '更新预测中…' : 'TimesFM 推理中…'}
          </Text>
          <Text type="secondary" style={{ display: 'block', marginTop: 4, fontSize: 12, opacity: 0.7 }}>
            {data ? '' : '服务启动时已预加载模型，首次约需 3-5 秒'}
          </Text>
        </div>
      ) : data ? (
        <>
          <Line {...config} height={200} />
          <div style={{ marginTop: 8, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 16, height: 3, background: '#f5642a', borderRadius: 1 }} />
              <Text type="secondary" style={{ fontSize: 12 }}>预测价格曲线</Text>
            </div>
            <Text type="secondary" style={{ fontSize: 11, marginLeft: 'auto', opacity: 0.6 }}>
              ⚠️ 仅基于历史价格形态，不构成投资建议
            </Text>
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Text type="secondary" style={{ fontSize: 13 }}>点击刷新加载预测</Text>
        </div>
      )}
    </Card>
  );
}
