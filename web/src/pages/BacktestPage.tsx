import { useState } from 'react';
import {
  Card, Button, Row, Col, Statistic, Table, Tag, Alert, Select, Space, Typography, Empty, Modal, message, InputNumber,
} from 'antd';
import {
  ExperimentOutlined, RiseOutlined, FallOutlined, QuestionCircleOutlined,
  SaveOutlined, FileTextOutlined,
} from '@ant-design/icons';
import { api } from '../api';
import SymbolSelect from '../components/SymbolSelect';

const { Text } = Typography;

const strategies = [
  { value: 'ma_cross', label: '均线金叉', desc: '短期均线上穿长期均线（金叉）买入，下穿（死叉）卖出。趋势跟踪型，适合单边趋势行情，震荡市易反复止损。' },
  { value: 'macd', label: 'MACD', desc: 'MACD 柱由负转正（DIF 上穿 DEA，金叉）买入，由正转负（死叉）卖出。兼顾趋势与动能，信号比纯均线略灵敏。' },
  { value: 'rsi', label: 'RSI', desc: 'RSI 跌破 30（超卖）买入，升破 70（超买）卖出。均值回归／反转型，适合区间震荡，强趋势中可能过早离场。' },
  { value: 'bollinger', label: '布林带', desc: '价格触及布林带下轨买入，触及上轨卖出。均值回归型，适合箱体震荡，单边突破行情中风险较高。' },
];

export default function BacktestPage() {
  const [code, setCode] = useState('');
  const [strategy, setStrategy] = useState('ma_cross');
  const [loading, setLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [params, setParams] = useState({ capital: 100000, commission: 0.03, slippage: 0.1 });
  const [helpOpen, setHelpOpen] = useState(false);
  const [reportPreview, setReportPreview] = useState<string | null>(null);
  const [reportFormat, setReportFormat] = useState<string>('markdown');

  const run = async (autoCode?: string) => {
    const c = autoCode || code;
    if (!c) { setError('请输入或选择股票代码'); return; }
    setLoading(true); setError(''); setReportPreview(null);
    try { const d = await api.backtest(c, strategy, undefined, undefined, params.capital, params.commission / 100, params.slippage / 100); setData(d.data); }
    catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  const previewReport = async () => {
    if (!data) return;
    setReportLoading(true);
    try {
      const d = await api.backtestReport(code || data.code, strategy, 'markdown');
      setReportPreview(d.content);
      setReportFormat(d.format);
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setReportLoading(false);
    }
  };

  const saveReport = async () => {
    if (!reportPreview) {
      message.warning('请先生成报告预览');
      return;
    }
    try {
      const d = await api.saveBacktestReport(code || data?.code, reportPreview, reportFormat);
      message.success(`报告已保存 (${d.report_id})`);
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const tradeColumns = [
    { title: '日期', dataIndex: 'date', width: 105,
      render: (v: string) => <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: '#64748b' }}>{v}</span>,
    },
    { title: '操作', dataIndex: 'action', width: 65,
      render: (v: string) => <Tag color={v === 'buy' ? 'red' : 'green'} style={{ borderRadius: 4 }}>{v === 'buy' ? '买入' : '卖出'}</Tag>,
    },
    { title: '价格', dataIndex: 'price', width: 85, align: 'right' as const,
      render: (v: number) => v?.toFixed(2) ?? '-',
    },
    { title: '数量', dataIndex: 'shares', width: 70, align: 'right' as const },
    { title: '金额', dataIndex: 'amount', width: 95, align: 'right' as const,
      render: (v: number) => v?.toFixed(2) ?? '-',
    },
    { title: '理由', dataIndex: 'reason' },
  ];

  const isPositive = (data?.total_return_pct ?? 0) >= 0;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>策略回测</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>历史数据验证交易策略</Text>
        </div>
      </div>

      {/* 参数区 */}
      <Card className="glass-card" style={{ marginBottom: 20 }}>
        <Space wrap>
          <SymbolSelect value={code} onChange={setCode} style={{ width: 200 }} />
          <Space size={4}>
            <Button type="text" shape="circle" icon={<QuestionCircleOutlined style={{ color: '#94a3b8' }} />}
              onClick={() => setHelpOpen(true)} title="策略说明" />
            <Select value={strategy} onChange={v => setStrategy(v)} options={strategies} style={{ width: 130 }} />
          </Space>
          <Button type="primary" icon={<ExperimentOutlined />} loading={loading} onClick={() => run()}>回测</Button>
        </Space>
      </Card>

      {/* 参数面板 */}
      <Card className="glass-card" size="small" style={{ marginBottom: 20 }} bodyStyle={{ padding: '10px 14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <Text type="secondary" style={{ fontSize: 11 }}>初始资金</Text>
            <InputNumber size="small" value={params.capital} min={10000} max={1e7} step={10000}
              onChange={v => setParams({ ...params, capital: v || 100000 })}
              style={{ width: 120 }} formatter={v => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 11 }}>佣金费率</Text>
            <InputNumber size="small" value={params.commission} min={0} max={1} step={0.01}
              onChange={v => setParams({ ...params, commission: v ?? 0.03 })}
              style={{ width: 100 }} addonAfter="%" />
          </div>
          <div>
            <Text type="secondary" style={{ fontSize: 11 }}>滑点</Text>
            <InputNumber size="small" value={params.slippage} min={0} max={1} step={0.01}
              onChange={v => setParams({ ...params, slippage: v ?? 0.1 })}
              style={{ width: 100 }} addonAfter="%" />
          </div>
        </div>
      </Card>

      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 80 }}>
          <div className="loading-breathe" style={{ marginBottom: 16 }}>
            <div className="dot-pulse" style={{ margin: '0 auto' }} />
          </div>
          <Text className="loading-text" style={{ fontSize: 13 }}>正在回测中...</Text>
        </div>
      ) : data ? (
        <Row gutter={[16, 16]}>
          {/* 左侧：参数 + 绩效 */}
          <Col xs={24} md={12}>
            <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>参数</span>} size="small" style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', gap: 16, fontSize: 13 }}>
                <div><Text type="secondary">股票</Text><div style={{ fontWeight: 500 }}>{data.code}</div></div>
                <div><Text type="secondary">策略</Text><div style={{ fontWeight: 500 }}>{strategy}</div></div>
                <div><Text type="secondary">区间</Text><div style={{ fontWeight: 500 }}>{data.start_date} ~ {data.end_date}</div></div>
              </div>
            </Card>

            <Row gutter={[8, 8]}>
              {[
                { title: '初始资金', value: data.initial_capital, unit: '', color: undefined },
                { title: '最终价值', value: data.final_value, unit: '', color: isPositive ? '#e53935' : '#43a047' },
                { title: '总收益', value: data.total_return_pct, unit: '%', color: isPositive ? '#e53935' : '#43a047', prefix: isPositive ? <RiseOutlined /> : <FallOutlined /> },
                { title: '最大回撤', value: data.max_drawdown, unit: '%', color: undefined },
                { title: '胜率', value: data.win_rate, unit: '%', color: undefined },
                { title: '夏普比率', value: data.sharpe_ratio, unit: '', color: undefined },
                { title: '交易次数', value: data.total_trades, unit: '', color: undefined },
                { title: '年化收益', value: (data.annual_return || 0) * 100, unit: '%', color: isPositive ? '#e53935' : '#43a047', prefix: isPositive ? <RiseOutlined /> : <FallOutlined /> },
              ].map((s, i) => (
                <Col xs={12} key={i}>
                  <Card className="stat-card" size="small">
                    <Statistic
                      title={<span style={{ color: '#64748b', fontSize: 12 }}>{s.title}</span>}
                      value={s.value}
                      precision={s.title === '交易次数' ? 0 : 2}
                      suffix={s.unit ? <span style={{ fontSize: 12, color: '#94a3b8' }}>{s.unit}</span> : ''}
                      prefix={s.prefix}
                      valueStyle={{ color: s.color ?? '#1a1a2e', fontWeight: 600, fontSize: 18 }}
                    />
                  </Card>
                </Col>
              ))}
            </Row>

            <div style={{ marginTop: 12 }}>
              <Space>
                <Button icon={<FileTextOutlined />} loading={reportLoading} onClick={previewReport}>
                  生成报告预览
                </Button>
                <Button type="primary" icon={<SaveOutlined />} onClick={saveReport} disabled={!reportPreview}>
                  保存报告
                </Button>
              </Space>
              <Text type="secondary" style={{ display: 'block', fontSize: 12, marginTop: 6 }}>
                点击"生成报告预览"查看 Markdown 格式报告，确认后点击"保存报告"持久化到报告列表
              </Text>
            </div>
          </Col>

          {/* 右侧：交易记录 */}
          <Col xs={24} md={12}>
            <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>交易记录</span>}
              bodyStyle={{ padding: 0 }}>
              {data.trades?.length > 0 ? (
                <Table dataSource={data.trades.slice().reverse()} columns={tradeColumns} rowKey="date"
                  pagination={{ defaultPageSize: 10, pageSizeOptions: [10, 20, 50], showSizeChanger: true }} size="small" scroll={{ y: 420 }} />
              ) : <Empty description="该策略未产生交易" style={{ padding: 40 }} />}
            </Card>
          </Col>

          {/* 报告预览 */}
          {reportPreview && (
            <Col span={24}>
              <Card className="glass-card" title={<span style={{ fontSize: 15, fontWeight: 600 }}>报告预览</span>}
                extra={
                  <Button type="primary" size="small" icon={<SaveOutlined />} onClick={saveReport}>
                    保存报告
                  </Button>
                }
              >
                <pre style={{
                  whiteSpace: 'pre-wrap', fontSize: 13, lineHeight: 1.7,
                  fontFamily: "'SF Mono', monospace", background: '#fafafa',
                  padding: 16, borderRadius: 8, maxHeight: 400, overflow: 'auto',
                  border: '1px solid rgba(0,0,0,0.06)',
                }}>
                  {reportPreview}
                </pre>
              </Card>
            </Col>
          )}
        </Row>
      ) : (
        <Card className="glass-card"><Text type="secondary">输入股票代码点击"回测"开始</Text></Card>
      )}

      <Modal title="📈 回测策略说明" open={helpOpen} onCancel={() => setHelpOpen(false)} footer={null}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 8 }}>
          {strategies.map(s => (
            <div key={s.value} style={{ borderLeft: '3px solid #f5642a', paddingLeft: 12 }}>
              <Text strong style={{ fontSize: 14, color: '#1a1a2e' }}>{s.label}</Text>
              <div style={{ fontSize: 13, color: '#64748b', marginTop: 2, lineHeight: 1.6 }}>{s.desc}</div>
            </div>
          ))}
          <Text type="secondary" style={{ fontSize: 12 }}>
            提示：回测仅基于历史数据，结果不代表未来收益，请结合实际谨慎参考。
          </Text>
        </div>
      </Modal>
    </div>
  );
}
