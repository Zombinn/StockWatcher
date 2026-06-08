import { useState, useEffect } from 'react';
import { Card, Button, Table, Tag, Input, Space, Typography, Empty, Popconfirm, message } from 'antd';
import { ReloadOutlined, PlusOutlined, StarOutlined, RiseOutlined, FallOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons';
import StockDetailDrawer from '../components/StockDetailDrawer';
import { api } from '../api';
import { analysisApi } from '../api/analysisApi';

const { Text } = Typography;

const MARKET_LABELS: Record<string, string> = { A: 'A股', HK: '港股', US: '美股' };

export default function WatchlistPanel() {
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<any[]>([]);
  const [adding, setAdding] = useState(false);
  const [newCode, setNewCode] = useState('');
  const [detailStock, setDetailStock] = useState<any>(null);
  const [watchlistCodes, setWatchlistCodes_] = useState<Set<string>>(new Set());

  const load = async () => {
    setLoading(true);
    try { const d = await api.getWatchlist(); setRows(d.data || []); setWatchlistCodes_(new Set((d.data || []).map((x: any) => x.code))); } catch (e: any) { message.error(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    const code = newCode.trim();
    if (!code) return;
    setAdding(true);
    try {
      const r = await api.addWatchlist(code);
      if (r.added) { message.success(`已添加 ${code.toUpperCase()}`); setNewCode(''); load(); }
      else message.info('该股票已在自选列表');
    } catch (e: any) { message.error(e.message); }
    finally { setAdding(false); }
  };

  const remove = async (code: string) => {
    try { await api.removeWatchlist(code); message.success(`已移除 ${code}`); load(); }
    catch (e: any) { message.error(e.message); }
  };

  const columns = [
    { title: '市场', dataIndex: 'market', width: 65,
      render: (v: string) => (
        <Tag color={v === 'A' ? 'blue' : v === 'HK' ? 'purple' : 'green'} style={{ borderRadius: 4, border: 'none' }}>
          {MARKET_LABELS[v] || v}
        </Tag>
      ),
    },
    { title: '代码', dataIndex: 'code', width: 90 },
    { title: '名称', dataIndex: 'name', width: 120 },
    { title: '现价', dataIndex: 'price', width: 90, align: 'right' as const,
      render: (v: number) => v ? <span style={{ fontWeight: 500, color: '#1a1a2e' }}>{v.toFixed(2)}</span> : '-' },
    { title: '涨跌', dataIndex: 'change_pct', width: 90,
      render: (v: number) => v != null
        ? <Tag color={v >= 0 ? 'red' : 'green'} icon={v >= 0 ? <RiseOutlined /> : <FallOutlined />} style={{ borderRadius: 4 }}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}%
          </Tag>
        : '-',
    },
    { title: '操作', width: 70, align: 'center' as const,
      render: (_: any, r: any) => (
        <Popconfirm title={`移除 ${r.code}?`} okText="移除" cancelText="取消" onConfirm={() => remove(r.code)}>
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Card className="glass-card" style={{ marginTop: 16 }}
      title={
        <Space size={8}>
          <StarOutlined style={{ color: '#f5642a' }} />
          <span style={{ fontSize: 15, fontWeight: 600 }}>自选股 ({rows.length})</span>
        </Space>
      }
      extra={
        <Space>
          <Input placeholder="代码 (如 600519 / AAPL)" value={newCode} size="small"
            onChange={e => setNewCode(e.target.value)} onPressEnter={add} style={{ width: 180 }} />
          <Button size="small" icon={<PlusOutlined />} loading={adding} onClick={add}>添加</Button>
          <Button size="small" type="text" icon={<ReloadOutlined />} loading={loading} onClick={load} />
        </Space>
      }>
      <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#fafafa', borderRadius: 8, border: '1px solid rgba(0,0,0,0.06)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <FileTextOutlined style={{ color: '#f5642a' }} />
          <Text style={{ fontSize: 13 }}>生成分析报告</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>基于自选股生成报告并保存到报告列表</Text>
        </div>
        <Button size="small" icon={<FileTextOutlined />} onClick={async () => {
          try {
            await api.analyze();
            message.success('分析已触发，完成后自动保存报告');
          } catch (e: any) { message.error(e.message); }
        }}>生成报告</Button>
      </div>
      {rows.length > 0 ? (
        <Table dataSource={rows} columns={columns} rowKey="code" pagination={false} size="small" loading={loading}
          scroll={{ x: 'max-content' }}
          onRow={(record: any) => ({
            style: { cursor: 'pointer' },
            onClick: async () => {
              setDetailStock({ code: record.code, name: record.name, price: record.price, change_pct: record.change_pct, loading: true });
              try {
                const res = await api.analyzeStock(record.code);
                setDetailStock({ ...(res.data || res), loading: false });
              } catch {
                setDetailStock({ code: record.code, name: record.name, price: record.price, change_pct: record.change_pct, loading: false });
              }
            },
          })} />
      ) : (
        <Empty description="暂无自选股，添加一只开始关注" />
      )}
    
      {/* 股票详情抽屉 */}
      <StockDetailDrawer
        stock={detailStock}
        inWatchlist={!!(detailStock && watchlistCodes.has(detailStock.code))}
        onClose={() => setDetailStock(null)}
      />
    </Card>
  );
}
