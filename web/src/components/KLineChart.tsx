import { useState, useEffect, useRef } from 'react';
import { Card, Spin, Typography, Tag, Space, Empty } from 'antd';
import { api } from '../api';

const { Text } = Typography;

interface Props {
  code: string;
  name?: string;
}

interface KLineItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  change_pct: number;
}

const CANVAS_W = 640;
const CANVAS_H = 380;
const CHART_H = 260;
const VOL_H = 80;
const PAD = { top: 24, right: 16, bottom: 20, left: 56 };

export default function KLineChart({ code }: Props) {
  const [items, setItems] = useState<KLineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!code) return;
    setLoading(true);
    api.stockKline(code, 60)
      .then((d: any) => setItems(d.items || []))
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [code]);

  useEffect(() => {
    if (items.length === 0) return;
    drawChart(canvasRef.current, items);
  }, [items]);

  if (loading) return <Card className="glass-card" bodyStyle={{ padding: 20, textAlign: 'center' }}><Spin /></Card>;
  if (error) return <Card className="glass-card" bodyStyle={{ padding: 20, textAlign: 'center' }}><Text type="danger">{error}</Text></Card>;
  if (items.length === 0) return <Card className="glass-card"><Empty description="暂无 K 线数据" /></Card>;

  return (
    <Card className="glass-card" bodyStyle={{ padding: 0, overflow: 'hidden' }}>
      <canvas ref={canvasRef} width={CANVAS_W} height={CANVAS_H}
        style={{ width: '100%', height: 'auto', display: 'block' }} />
    </Card>
  );
}

function drawChart(canvas: HTMLCanvasElement | null, items: KLineItem[]) {
  if (!canvas || items.length === 0) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const w = CANVAS_W * dpr;
  const h = CANVAS_H * dpr;
  canvas.width = w;
  canvas.height = h;
  canvas.style.width = `${CANVAS_W}px`;
  canvas.style.height = `${CANVAS_H}px`;
  ctx.scale(dpr, dpr);

  const chartW = CANVAS_W - PAD.left - PAD.right;
  const chartH = CHART_H - PAD.top - PAD.bottom;
  const volH = VOL_H - 4;
  const volY = CHART_H + 2;
  const n = items.length;
  const candleW = Math.min(Math.max(chartW / n - 1, 1), 8);
  const gap = Math.max(1, candleW < 3 ? 0.5 : 1);

  const prices = items.flatMap(i => [i.high, i.low, i.open, i.close]);
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const priceRange = maxPrice - minPrice || 1;

  const maxVol = Math.max(...items.map(i => i.volume), 1);

  // Clear
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

  // Y-axis price labels
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = PAD.top + chartH - (chartH * i / 4);
    const val = minPrice + priceRange * i / 4;
    ctx.fillText(val.toFixed(2), PAD.left - 6, y + 3);
    ctx.strokeStyle = 'rgba(0,0,0,0.04)';
    ctx.beginPath();
    ctx.moveTo(PAD.left, y);
    ctx.lineTo(CANVAS_W - PAD.right, y);
    ctx.stroke();
  }

  // Draw candles
  items.forEach((item, i) => {
    const x = PAD.left + (chartW * i / n) + gap;
    const isUp = item.close >= item.open;

    const yHigh = PAD.top + chartH - ((item.high - minPrice) / priceRange * chartH);
    const yLow = PAD.top + chartH - ((item.low - minPrice) / priceRange * chartH);
    const yOpen = PAD.top + chartH - ((item.open - minPrice) / priceRange * chartH);
    const yClose = PAD.top + chartH - ((item.close - minPrice) / priceRange * chartH);

    ctx.strokeStyle = isUp ? '#e53935' : '#43a047';
    ctx.lineWidth = Math.max(0.5, candleW * 0.2);
    ctx.beginPath();
    ctx.moveTo(x + candleW / 2, yHigh);
    ctx.lineTo(x + candleW / 2, yLow);
    ctx.stroke();

    if (isUp) {
      ctx.fillStyle = '#e53935';
      ctx.fillRect(x, yClose, candleW, Math.max(1, yOpen - yClose));
    } else {
      ctx.fillStyle = '#43a047';
      ctx.fillRect(x, yOpen, candleW, Math.max(1, yClose - yOpen));
    }

    // Volume bar
    const vH = (item.volume / maxVol) * volH;
    ctx.fillStyle = isUp ? 'rgba(229,57,53,0.3)' : 'rgba(67,160,71,0.3)';
    ctx.fillRect(x, volY + volH - vH, candleW, vH);
  });

  // Volume Y-axis
  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px system-ui';
  ctx.textAlign = 'right';
  const volMid = maxVol / 2;
  ctx.fillText(formatVol(maxVol), PAD.left - 6, volY + 10);
  ctx.fillText(formatVol(volMid), PAD.left - 6, volY + volH / 2 + 3);

  // X-axis date labels (every 10th)
  ctx.textAlign = 'center';
  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px system-ui';
  const step = Math.max(1, Math.floor(n / 6));
  for (let i = 0; i < n; i += step) {
    const x = PAD.left + (chartW * i / n) + candleW / 2;
    ctx.fillText(formatDate(items[i].date), x, CHART_H + volH + 14);
  }
}

function formatVol(v: number): string {
  if (v >= 1e8) return `${(v / 1e8).toFixed(1)}亿`;
  if (v >= 1e4) return `${(v / 1e4).toFixed(0)}万`;
  return v.toFixed(0);
}

function formatDate(d: string): string {
  return d.slice(5, 10).replace('-', '/');
}
