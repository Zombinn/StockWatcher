import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Spin, Typography, Tag, Space, Empty, Segmented } from 'antd';
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
}

const PERIOD_LABELS = ['近 60 天', '近 120 天', '近 250 天'];
const PERIOD_COUNTS: Record<string, number> = { '近 60 天': 60, '近 120 天': 120, '近 250 天': 250 };
const MA_CONFIGS = [
  { period: 5,  color: '#f5642a' },
  { period: 10, color: '#1e88e5' },
  { period: 20, color: '#8e24aa' },
] as const;
const CHART_H = 260;
const VOL_H = 72;
const PAD = { top: 28, right: 16, bottom: 24, left: 56 };

function layout(canvasW: number) {
  return {
    chartW: canvasW - PAD.left - PAD.right,
    chartH: CHART_H - PAD.top - PAD.bottom,
    volH: VOL_H - 4,
    volY: CHART_H + 4,
  };
}

export default function KLineChart({ code }: Props) {
  const [period, setPeriod] = useState<string>('近 60 天');
  const [items, setItems] = useState<KLineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tooltip, setTooltip] = useState<{ x: number; item: KLineItem; idx: number } | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<KLineItem[]>([]);
    itemsRef.current = items;

  useEffect(() => {
    if (!code) return;
    setLoading(true);
    setTooltip(null);
    const count = PERIOD_COUNTS[period] || 60;
    api.stockKline(code, count)
      .then((d: any) => setItems(d.items || []))
      .catch((e: any) => setError(e.message))
      .finally(() => setLoading(false));
  }, [code, period]);

  useEffect(() => {
    if (items.length === 0) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawChart(canvas, items, tooltip);
  }, [items, tooltip]);

const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const items = itemsRef.current;
    if (!canvas || items.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width / (window.devicePixelRatio || 1);
    const mx = (e.clientX - rect.left) * scaleX;
    const { chartW } = layout(canvas.width);
    const n = items.length;
    const idx = Math.round((mx - PAD.left) / chartW * (n - 1));
    if (idx < 0 || idx >= n) { setTooltip(null); return; }
    setTooltip({ x: PAD.left + (chartW * idx / n), item: items[idx], idx });
  }, []);

  const handleMouseLeave = useCallback(() => setTooltip(null), []);

  if (loading) return <Card className="glass-card" bodyStyle={{ padding: 20, textAlign: 'center' }}><Spin /></Card>;
  if (error) return <Card className="glass-card" bodyStyle={{ padding: 20, textAlign: 'center' }}><Text type="danger">{error}</Text></Card>;
  if (items.length === 0) return <Card className="glass-card"><Empty description="暂无 K 线数据" /></Card>;

  return (
    <Card className="glass-card" bodyStyle={{ padding: 0, overflow: 'visible' }}>
      <div style={{ padding: '8px 12px 4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {/* MA 图例 */}
        <Space size={12}>
          {MA_CONFIGS.map(({ period: p, color }) => (
            <span key={p} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#64748b' }}>
              <span style={{ display: 'inline-block', width: 20, height: 2, background: color, borderRadius: 1 }} />
              MA{p}
            </span>
          ))}
        </Space>
        <Segmented
          value={period}
          onChange={(v) => setPeriod(v as string)}
          options={PERIOD_LABELS}
          size="small"
        />
      </div>

      <div ref={containerRef} style={{ position: 'relative' }}>
        <canvas
          ref={canvasRef}

          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{ width: '100%', height: 'auto', display: 'block', cursor: "default" }}
        />
        {tooltip && (
          <div style={{
            position: 'absolute',
            left: tooltip.x > ((containerRef.current?.clientWidth || 400) / 2) ? Math.max(4, tooltip.x - 180) : tooltip.x + 16,
            top: 4,
            background: '#fff',
            border: '1px solid rgba(0,0,0,0.12)',
            borderRadius: 8,
            padding: '8px 12px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
            fontSize: 12,
            lineHeight: 1.8,
            zIndex: 10,
            pointerEvents: 'none',
            minWidth: 160,
          }}>
            <div style={{ fontWeight: 600, marginBottom: 2, color: '#1a1a2e' }}>{tooltip.item.date}</div>
            {[
              ['开', tooltip.item.open],
              ['高', tooltip.item.high],
              ['低', tooltip.item.low],
              ['收', tooltip.item.close],
            ].map(([label, val]) => (
              <div key={label as string} style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                <span style={{ color: '#64748b' }}>{label as string}</span>
                <span style={{ color: tooltip.item.open >= tooltip.item.close ? '#43a047' : '#e53935' }}>
                  {(val as number).toFixed(2)}
                </span>
              </div>
            ))}
            <div style={{
              display: 'flex', justifyContent: 'space-between', gap: 16,
              borderTop: '1px solid rgba(0,0,0,0.06)', marginTop: 4, paddingTop: 4,
            }}>
              <span style={{ color: '#64748b' }}>涨跌幅</span>
              <span style={{ color: tooltip.item.close >= itemsRef.current[Math.max(0, tooltip.idx - 1)].close ? '#e53935' : '#43a047', fontWeight: 600 }}>
                {(() => {
                  const prev = itemsRef.current[Math.max(0, tooltip.idx - 1)].close;
                  const pct = (tooltip.item.close - prev) / prev * 100;
                  return (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
                })()}
              </span>
            </div>
            <div style={{
              display: 'flex', justifyContent: 'space-between', gap: 16,
              borderTop: '1px solid rgba(0,0,0,0.06)', marginTop: 4, paddingTop: 4,
            }}>
              <span style={{ color: '#64748b' }}>成交量</span>
              <span style={{ fontWeight: 500 }}>
                {(tooltip.item.volume >= 1e8 ? (tooltip.item.volume / 1e8).toFixed(2) + '亿' : tooltip.item.volume >= 1e4 ? (tooltip.item.volume / 1e4).toFixed(0) + '万' : tooltip.item.volume.toFixed(0))}
              </span>
            </div>
            <div style={{ borderTop: '1px solid rgba(0,0,0,0.06)', marginTop: 4, paddingTop: 4 }}>
              {MA_CONFIGS.map(({ period: p, color }) => {
                const maVals = computeMA(itemsRef.current, p);
                const v = maVals[tooltip.idx];
                return v !== null ? (
                  <div key={p} style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                    <span style={{ color }}>MA{p}</span>
                    <span style={{ fontWeight: 500 }}>{v.toFixed(2)}</span>
                  </div>
                ) : null;
              })}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

function computeMA(items: KLineItem[], period: number): (number | null)[] {
  return items.map((_, i) => {
    if (i < period - 1) return null;
    const sum = items.slice(i - period + 1, i + 1).reduce((a, b) => a + b.close, 0);
    return sum / period;
  });
}

function drawChart(canvas: HTMLCanvasElement, items: KLineItem[], tooltip: { idx: number } | null) {
  if (!canvas || items.length === 0) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const w = rect.width * dpr;
  const h = (CHART_H + VOL_H + PAD.bottom) * dpr;
  canvas.width = w;
  canvas.height = h;
  ctx.scale(dpr, dpr);

  const cw = rect.width;
  const ch = CHART_H + VOL_H + PAD.bottom;
  const L = layout(cw);
  const n = items.length;
  const candleW = Math.min(Math.max(L.chartW / n - 1, 1), 8);
  const gap = Math.max(1, candleW < 3 ? 0.5 : 1);

  const prices = items.flatMap(i => [i.high, i.low]);
  const maxPrice = Math.max(...prices);
  const minPrice = Math.min(...prices);
  const pad = (maxPrice - minPrice) * 0.05 || 1;
  const pMin = minPrice - pad;
  const pMax = maxPrice + pad;
  const pRange = pMax - pMin || 1;

  const maxVol = Math.max(...items.map(i => i.volume), 1);

  function yPrice(v: number) { return PAD.top + L.chartH - ((v - pMin) / pRange * L.chartH); }
  function yVol(v: number) { return L.volY + L.volH - (v / maxVol * L.volH); }

  ctx.clearRect(0, 0, cw, ch);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, cw, ch);

  // Grid + Y-axis
  ctx.fillStyle = '#94a3b8';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const y = PAD.top + L.chartH * (1 - i / 4);
    const val = pMin + pRange * i / 4;
    ctx.fillText(val.toFixed(2), PAD.left - 6, y + 3);
    ctx.strokeStyle = 'rgba(0,0,0,0.04)';
    ctx.beginPath(); ctx.moveTo(PAD.left, y); ctx.lineTo(cw - PAD.right, y); ctx.stroke();
  }

  // Volume axis
  ctx.textAlign = 'right';
  ctx.font = '9px system-ui';
  ctx.fillText(formatVol(maxVol), PAD.left - 6, L.volY + 10);
  ctx.fillText(formatVol(maxVol / 2), PAD.left - 6, L.volY + L.volH / 2 + 3);

  // Candles
  for (let i = 0; i < n; i++) {
    const item = items[i];
    const x = PAD.left + (L.chartW * i / n) + gap;
    const isUp = item.close >= item.open;

    const yH = yPrice(item.high);
    const yL = yPrice(item.low);
    const yO = yPrice(item.open);
    const yC = yPrice(item.close);

    ctx.strokeStyle = isUp ? '#e53935' : '#43a047';
    ctx.lineWidth = Math.max(0.5, candleW * 0.25);
    ctx.beginPath();
    ctx.moveTo(x + candleW / 2, yH);
    ctx.lineTo(x + candleW / 2, yL);
    ctx.stroke();

    if (isUp) {
      ctx.fillStyle = '#e53935';
      ctx.fillRect(x, yC, candleW, Math.max(1, yO - yC));
    } else {
      ctx.fillStyle = '#43a047';
      ctx.fillRect(x, yO, candleW, Math.max(1, yC - yO));
    }

    ctx.fillStyle = isUp ? 'rgba(229,57,53,0.25)' : 'rgba(67,160,71,0.25)';
    ctx.fillRect(x, yVol(item.volume), candleW, L.volH - (yVol(item.volume) - L.volY));
  }

  // MA lines
  for (const { period: maPeriod, color } of MA_CONFIGS) {
    const maValues = computeMA(items, maPeriod);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.setLineDash([]);
    ctx.beginPath();
    let started = false;
    for (let i = 0; i < n; i++) {
      const v = maValues[i];
      if (v === null) continue;
      const x = PAD.left + (L.chartW * i / n) + candleW / 2;
      const y = yPrice(v);
      if (!started) { ctx.moveTo(x, y); started = true; }
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  if (tooltip && tooltip.idx >= 0 && tooltip.idx < n) {
    const i = tooltip.idx;
    const x = PAD.left + (L.chartW * i / n) + candleW / 2;
    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath(); ctx.moveTo(x, PAD.top); ctx.lineTo(x, L.volY + L.volH); ctx.stroke();
    ctx.setLineDash([]);

    const item = items[i];
    const isUp = item.close >= item.open;
    ctx.strokeStyle = isUp ? '#e53935' : '#43a047';
    ctx.lineWidth = 2;
    const topY = yPrice(Math.max(item.high, item.low, item.open, item.close));
    const botY = yPrice(Math.min(item.high, item.low, item.open, item.close));
    ctx.strokeRect(x - candleW / 2 - 1.5, topY - 1, candleW + 3, botY - topY + 2);
  }


  ctx.textAlign = 'center';
  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px system-ui';
  const step = Math.max(1, Math.floor(n / 6));
  for (let i = 0; i < n; i += step) {
    const x = PAD.left + (L.chartW * i / n) + candleW / 2;
    ctx.fillText(items[i].date.slice(5, 10).replace('-', '/'), x, CHART_H + L.volH + 16);
  }
}



function formatVol(v: number): string {
  if (v >= 1e8) return `${(v / 1e8).toFixed(1)}亿`;
  if (v >= 1e4) return `${(v / 1e4).toFixed(0)}万`;
  return v.toFixed(0);
}
