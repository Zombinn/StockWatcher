import { useState, useEffect } from 'react';
import {
  Card, Table, Button, Space, Tag, Drawer, Typography,
  Popconfirm, message, Empty, Alert,
} from 'antd';
import {
  DeleteOutlined, ReloadOutlined, FileTextOutlined,
  ClockCircleOutlined, BarChartOutlined,
} from '@ant-design/icons';
import { renderMarkdown } from '../utils/markdown';
import { api } from '../api';

const { Text, Title } = Typography;

export default function ReportPage() {
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [detail, setDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');

  const load = async (p = page) => {
    setLoading(true);
    setError('');
    try {
      const d = await api.listReports(p, 10);
      setItems(d.items || []);
      setTotal(d.total || 0);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const onPageChange = (p: number) => {
    setPage(p);
    setSelectedIds([]);
    load(p);
  };

  const openDetail = async (rid: string) => {
    setDetailLoading(true);
    setDetail(null);
    setDetailError('');
    try {
      const d = await api.getReport(rid);
      setDetail(d.data);
    } catch (e: any) {
      setDetailError(e.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDelete = async (rid: string) => {
    try {
      await api.deleteReport(rid);
      message.success('已删除');
      load(page);
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) return;
    try {
      const d = await api.deleteReportsBatch(selectedIds);
      message.success(`已删除 ${d.deleted} 条`);
      setSelectedIds([]);
      load(page);
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (t: string, record: any) => (
        <a onClick={() => openDetail(record.id)} style={{ fontWeight: 500 }}>
          <FileTextOutlined style={{ marginRight: 6, color: '#f5642a' }} />
          {t}
        </a>
      ),
    },
    {
      title: '股票数',
      dataIndex: 'stock_count',
      key: 'stock_count',
      width: 90,
      render: (v: number) => <Tag>{v} 只</Tag>,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (t: string) => (
        <span style={{ color: '#64748b', fontSize: 13 }}>
          <ClockCircleOutlined style={{ marginRight: 4 }} />
          {t}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: any) => (
        <Popconfirm title="确认删除这条报告？" onConfirm={() => handleDelete(record.id)} okText="删除" cancelText="取消">
          <Button type="text" danger size="small" icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <BarChartOutlined style={{ fontSize: 20, color: '#f5642a' }} />
          <span style={{ fontSize: 18, fontWeight: 600, color: '#1a1a2e' }}>分析报告</span>
        </div>
        <Space>
          {selectedIds.length > 0 && (
            <Popconfirm
              title={`确认删除选中的 ${selectedIds.length} 条报告？`}
              onConfirm={handleBatchDelete}
              okText="删除"
              cancelText="取消"
            >
              <Button danger icon={<DeleteOutlined />}>
                删除选中 ({selectedIds.length})
              </Button>
            </Popconfirm>
          )}
          <Button icon={<ReloadOutlined />} onClick={() => load(page)} loading={loading}>
            刷新
          </Button>
        </Space>
      </div>

      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

      <Card bodyStyle={{ padding: 0 }}>
        <Table
          rowKey="id"
          dataSource={items}
          columns={columns}
          loading={loading}
          pagination={{
            current: page,
            pageSize: 10,
            total,
            onChange: onPageChange,
            showTotal: (t) => `共 ${t} 条`,
          }}
          rowSelection={{
            selectedRowKeys: selectedIds,
            onChange: (keys) => setSelectedIds(keys as string[]),
          }}
          locale={{ emptyText: <Empty description="暂无分析报告" /> }}
          size="middle"
        />
      </Card>

      {/* 详情抽屉 — 宽度加大 + Markdown 渲染 */}
      <Drawer
        title={
          <span>
            <FileTextOutlined style={{ marginRight: 8, color: '#f5642a' }} />
            {detail?.title || '报告详情'}
          </span>
        }
        placement="right"
        width="min(75vw, 800px)"
        open={!!detail}
        onClose={() => setDetail(null)}
        loading={detailLoading}
      >
        {detailError && <Alert type="error" message={detailError} showIcon />}
        {detail && (
          <div style={{ paddingBottom: 40 }}>
            {/* Meta */}
            <div style={{
              display: 'flex',
              gap: 24,
              marginBottom: 20,
              padding: '12px 16px',
              background: '#fafafa',
              borderRadius: 8,
              border: '1px solid rgba(0,0,0,0.06)',
            }}>
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>时间</Text>
                <div style={{ fontWeight: 500, marginTop: 2 }}>{detail.created_at}</div>
              </div>
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>股票数</Text>
                <div style={{ fontWeight: 500, marginTop: 2 }}>{detail.stock_count} 只</div>
              </div>
            </div>

            {/* Stock list */}
            {detail.details?.stocks?.length > 0 && (
              <div style={{ marginBottom: 20 }}>
                <Title level={5} style={{ marginBottom: 8 }}>股票列表</Title>
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                }}>
                  {detail.details.stocks.map((s: any) => (
                    <Tag
                      key={s.code}
                      style={{
                        padding: '2px 10px',
                        fontSize: 13,
                        borderRadius: 6,
                      }}
                      color={s.score >= 70 ? 'success' : s.score >= 40 ? 'warning' : 'error'}
                    >
                      {s.name || s.code}
                      <span style={{ marginLeft: 6, fontWeight: 600 }}>
                        {s.change_pct >= 0 ? '+' : ''}{s.change_pct?.toFixed(2)}%
                      </span>
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            {/* Full report with Markdown rendering */}
            {(detail.details?.report || detail.details?.details?.report) && (
              <div>
                <Title level={5} style={{ marginBottom: 12 }}>完整报告</Title>
                <div style={{
                  background: '#fafafa',
                  padding: '16px 20px',
                  borderRadius: 8,
                  border: '1px solid rgba(0,0,0,0.06)',
                }}>
                  {renderMarkdown(detail.details.report || detail.details.details.report)}
                </div>
              </div>
            )}

            {/* LLM analysis from CLI runs */}
            {detail.details?.llm && (
              <div style={{ marginTop: 20 }}>
                <Title level={5} style={{ marginBottom: 12 }}>AI 解读</Title>
                {Object.entries(detail.details.llm).map(([code, llm]: [string, any]) => (
                  <div key={code} style={{
                    marginBottom: 12,
                    padding: 12,
                    background: '#fafafa',
                    borderRadius: 8,
                    border: '1px solid rgba(0,0,0,0.06)',
                  }}>
                    <Text strong style={{ fontSize: 14 }}>{code}</Text>
                    <div style={{ marginTop: 8, fontSize: 13, lineHeight: 1.7 }}>
                      {renderMarkdown(
                        Object.entries(llm)
                          .filter(([k]) => k !== 'stock_code')
                          .map(([k, v]) => `**${k}**: ${v}`)
                          .join('\n\n')
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}
