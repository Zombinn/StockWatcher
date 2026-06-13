import { useState, useEffect } from 'react';
import { Card, Button, Row, Col, Statistic, Table, Tag, Alert, Typography, Modal, Input, InputNumber, Space, Select, Empty, message, Popconfirm } from 'antd';
import { ReloadOutlined, PlusOutlined, WalletOutlined, RiseOutlined, FallOutlined, ImportOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { api } from '../api';
import { useWatchlist } from '../hooks/useWatchlist';
import StockDetailDrawer from '../components/StockDetailDrawer';
import WatchlistPanel from './WatchlistPanel';

const { Text } = Typography;

const MARKET_LABELS: Record<string, string> = { A: 'A股', HK: '港股', US: '美股' };
const MARKET_COLORS: Record<string, string> = { A: '#1e88e5', HK: '#8e24aa', US: '#43a047' };

export default function PortfolioPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importText, setImportText] = useState('');
  const [importing, setImporting] = useState(false);
  const [detailStock, setDetailStock] = useState<any>(null);
  const { watchlistCodes, loadWatchlist } = useWatchlist();
  const [filterMarket, setFilterMarket] = useState<string>('');
  const [form, setForm] = useState({ code: '', quantity: 100, cost_price: 0, market: '' });
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({ code: '', name: '', quantity: 0, cost_price: 0 });

  const load = async () => {
    setLoading(true); setError('');
    try { const d = await api.getPortfolio(); setData(d.data); } catch (e: any) { setError(e.message); }
    await loadWatchlist();
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    await api.addPosition(form.code, form.quantity, form.cost_price, '', form.market);
    setModalOpen(false);
    setForm({ code: '', quantity: 100, cost_price: 0, market: '' });
    load();
  };

  const doImport = async () => {
    if (!importText.trim()) { message.warning('请粘贴或上传持仓内容'); return; }
    setImporting(true);
    try {
      const r = await api.importPositions(importText);
      message.success(`成功导入 ${r.imported} 条${r.errors?.length ? `，${r.errors.length} 条跳过` : ''}`);
      setImportOpen(false); setImportText('');
      load();
    } catch (e: any) { message.error(e.message); }
    finally { setImporting(false); }
  };

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImportText(String(reader.result || ''));
    reader.readAsText(file);
  };

  const filteredPositions = (data?.positions || []).filter((p: any) => {
    if (!filterMarket) return true;
    return p.market === filterMarket;
  });

  const marketStats: Record<string, { count: number; value: number }> = {};
  for (const p of data?.positions || []) {
    const m = p.market || 'A';
    if (!marketStats[m]) marketStats[m] = { count: 0, value: 0 };
    marketStats[m].count += p.quantity;
    marketStats[m].value += p.market_value;
  }

  const columns = [
    { title: '市场', dataIndex: 'market', width: 65,
      render: (v: string) => (
        <Tag color={v === 'A' ? 'blue' : v === 'HK' ? 'purple' : 'green'} style={{ borderRadius: 4, border: 'none' }}>
          {MARKET_LABELS[v] || v}
        </Tag>
      ),
    },
    { title: '代码', dataIndex: 'code', width: 85 },
    { title: '名称', dataIndex: 'name', width: 110 },
    { title: '持仓', dataIndex: 'quantity', width: 70, render: (v: number) => <span style={{ fontWeight: 500, color: '#1a1a2e' }}>{v}</span> },
    { title: '成本', dataIndex: 'cost_price', width: 85, render: (v: number) => v?.toFixed(2) ?? '-', align: 'right' as const },
    { title: '现价', dataIndex: 'current_price', width: 85, render: (v: number) => v?.toFixed(2) ?? '-', align: 'right' as const },
    { title: '市值', dataIndex: 'market_value', width: 95, render: (v: number) => v?.toFixed(2) ?? '-', align: 'right' as const },
    {
      title: '盈亏', dataIndex: 'profit_pct', width: 85,
      render: (v: number) => v != null
        ? <Tag color={v >= 0 ? 'red' : 'green'} icon={v >= 0 ? <RiseOutlined /> : <FallOutlined />} style={{ borderRadius: 4 }}>
            {v >= 0 ? '+' : ''}{v.toFixed(2)}%
          </Tag>
        : '-',
    },
    { title: '占比', dataIndex: 'weight', width: 70, render: (v: number) => v != null ? `${v.toFixed(1)}%` : '-', align: 'right' as const },
    { title: '操作', width: 60, align: 'center' as const,
      render: (_: any, r: any) => (
        <Space size={0}>
          <Button type="text" size="small" icon={<EditOutlined style={{ color: '#f5642a' }} />
          } onClick={(e) => { e.stopPropagation(); setEditForm({ code: r.code, name: r.name, quantity: r.quantity, cost_price: r.cost_price }); setEditOpen(true); }} />
          <Popconfirm title={`清仓 ${r.code}?`} okText="清仓" cancelText="取消"
            onConfirm={async (e?: any) => { e?.stopPropagation(); try { await api.removePosition(r.code); message.success('已清仓'); load(); } catch (e: any) { message.error(e.message); } }}
            onCancel={(e?: any) => e?.stopPropagation()}>
            <Button type="text" size="small" danger icon={<DeleteOutlined />}
              onClick={(e) => e.stopPropagation()} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>持仓管理</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>资产概览与盈亏跟踪</Text>
        </div>
        <Space>
          <Select
            value={filterMarket}
            onChange={setFilterMarket}
            options={[
              { value: '', label: '全市场' },
              { value: 'A', label: '🇨🇳 A股' },
              { value: 'HK', label: '🇭🇰 港股' },
              { value: 'US', label: '🇺🇸 美股' },
            ]}
            style={{ width: 110 }}
          />
          <Button icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>添加</Button>
          <Button icon={<ImportOutlined />} onClick={() => setImportOpen(true)}>导入</Button>
          <Button type="primary" icon={<ReloadOutlined />} loading={loading} onClick={load}>刷新</Button>
        </Space>
      </div>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <div className="loading-breathe" style={{ marginBottom: 16 }}>
            <div className="dot-pulse" style={{ margin: '0 auto' }} />
          </div>
          <Text className="loading-text" style={{ fontSize: 13 }}>正在加载持仓...</Text>
        </div>
      ) : data ? (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={12} sm={6}>
              <Card className="stat-card" size="small">
                <Statistic title={<span style={{ color: '#64748b' }}>总市值</span>} value={data.total_market_value} precision={2}
                  prefix={<WalletOutlined style={{ opacity: 0.4, marginRight: 4, color: '#f5642a' }} />}
                  valueStyle={{ color: '#1a1a2e', fontWeight: 600, fontSize: 22 }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="stat-card" size="small">
                <Statistic title={<span style={{ color: '#64748b' }}>总收益</span>} value={data.total_profit} precision={2}
                  valueStyle={{
                    color: data.total_profit >= 0 ? '#e53935' : '#43a047',
                    fontWeight: 600, fontSize: 22,
                  }}
                  suffix={<span style={{ fontSize: 14, color: data.total_profit_pct >= 0 ? '#e53935' : '#43a047' }}>
                    ({data.total_profit_pct >= 0 ? '+' : ''}{data.total_profit_pct?.toFixed(2) ?? '0.00'}%)
                  </span>}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="stat-card" size="small">
                <Statistic title={<span style={{ color: '#64748b' }}>风险评分</span>} value={data.risk_score} suffix="/100"
                  valueStyle={{
                    color: data.risk_score > 60 ? '#e53935' : data.risk_score > 30 ? '#f9a825' : '#43a047',
                    fontWeight: 600, fontSize: 22,
                  }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card className="stat-card" size="small"
                title={<span style={{ fontSize: 13, color: '#64748b' }}>市场分布</span>}>
                {Object.keys(marketStats).length > 0 ? Object.entries(marketStats).map(([m, s]: any) => {
                  const tagColor = m === 'A' ? 'blue' : m === 'HK' ? 'purple' : 'green';
                  return (
                    <div key={m} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13, padding: '2px 0' }}>
                      <Tag color={tagColor} style={{ borderRadius: 4, border: 'none' }}>{MARKET_LABELS[m] || m}</Tag>
                      <span style={{ color: '#64748b' }}>{s.count} 只 / ${s.value.toFixed(0)}</span>
                    </div>
                  );
                }) : <Text type="secondary">无持仓</Text>}
              </Card>
            </Col>
          </Row>
          {data.suggestion && (
            <Alert type="info" message={<span><strong style={{ color: '#1e88e5' }}>建议：</strong>{data.suggestion}</span>} showIcon style={{ marginBottom: 16 }} closable />
          )}
          <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>持仓明细 ({filteredPositions.length} 只)</span>}>
            {filteredPositions.length > 0 ? (
              <Table dataSource={filteredPositions} columns={columns} rowKey="code" pagination={{ defaultPageSize: 10, pageSizeOptions: [10, 20, 50], showSizeChanger: true }} size="small"
                onRow={(record: any) => ({
                  style: { cursor: 'pointer' },
                  onClick: async () => {
                    setDetailStock({ code: record.code, name: record.name, price: record.current_price, change_pct: record.profit_pct, loading: true });
                    try {
                      const res = await api.analyzeStock(record.code);
                      setDetailStock({ ...(res.data || res), loading: false });
                    } catch {
                      setDetailStock({ code: record.code, name: record.name, price: record.current_price, change_pct: record.profit_pct, loading: false });
                    }
                  },
                })}
              />
            ) : (
              <Empty description={filterMarket ? '该市场暂无持仓' : '暂无持仓，点击"添加"按钮添加'} />
            )}
          </Card>

          {/* 自选股（独立存储，无成本/盈亏/占比） */}
          <WatchlistPanel />
        </>
      ) : (
        <Card className="glass-card"><Empty description="点击「刷新持仓」加载数据" /></Card>
      )}

      <Modal title="添加持仓" open={modalOpen} onOk={add} onCancel={() => setModalOpen(false)}
        okText="添加" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>股票代码</div>
            <Input placeholder="例: 600519 / TSLA / 00700.HK" value={form.code}
              onChange={e => setForm({ ...form, code: e.target.value })} />
          </div>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>市场（可选）</div>
            <Select value={form.market} onChange={v => setForm({ ...form, market: v })}
              options={[
                { value: '', label: '自动检测 (推荐)' },
                { value: 'A', label: '🇨🇳 A股' },
                { value: 'HK', label: '🇭🇰 港股' },
                { value: 'US', label: '🇺🇸 美股' },
              ]} style={{ width: '100%' }} placeholder="选择市场" />
          </div>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>数量</div>
            <InputNumber placeholder="输入持仓数量" value={form.quantity} min={1}
              onChange={v => setForm({ ...form, quantity: v || 0 })} style={{ width: '100%' }} />
          </div>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>成本价</div>
            <InputNumber placeholder="输入每股成本价" value={form.cost_price} min={0} step={0.01}
              onChange={v => setForm({ ...form, cost_price: v || 0 })} style={{ width: '100%' }} />
          </div>
        </div>
      </Modal>

      <Modal title={`编辑持仓 - ${editForm.code}`} open={editOpen}
        onOk={async () => {
          try {
            await api.updatePosition(editForm.code, editForm.quantity, editForm.cost_price, editForm.name);
            message.success('已更新');
            setEditOpen(false);
            load();
          } catch (e: any) { message.error(e.message); }
        }}
        onCancel={() => setEditOpen(false)} okText="保存" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>名称</div>
            <Input value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} />
          </div>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>数量</div>
            <InputNumber value={editForm.quantity} min={1} style={{ width: '100%' }}
              onChange={v => setEditForm({ ...editForm, quantity: v || 0 })} />
          </div>
          <div>
            <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>成本价</div>
            <InputNumber value={editForm.cost_price} min={0} step={0.01} style={{ width: '100%' }}
              onChange={v => setEditForm({ ...editForm, cost_price: v || 0 })} />
          </div>
        </div>
      </Modal>

      <Modal title="批量导入持仓" open={importOpen} onOk={doImport} confirmLoading={importing}
        onCancel={() => setImportOpen(false)} okText="导入" cancelText="取消">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: 13 }}>
            每行一条，格式：<Text code>代码,数量,成本价,名称(可选)</Text>。支持逗号/制表符/空格分隔，可直接从 Excel/表格复制粘贴，表头自动忽略。
          </Text>
          <Input type="file" accept=".csv,.txt,.tsv" onChange={onFile} />
          <Input.TextArea rows={8} value={importText} onChange={e => setImportText(e.target.value)}
            placeholder={'600519,100,1700.5,贵州茅台\nAAPL,50,180.3,Apple\n00700.HK,200,380,腾讯控股'} />
        </div>
      </Modal>

      {/* 股票详情抽屉 */}
      <StockDetailDrawer
        stock={detailStock}
        inWatchlist={!!(detailStock && watchlistCodes.has(detailStock.code))}
        onClose={() => setDetailStock(null)}
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
