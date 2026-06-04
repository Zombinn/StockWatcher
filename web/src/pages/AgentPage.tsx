import { useState } from 'react';
import { Card, Input, Button, Alert, Typography, Space, Spin, Tag } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, BulbOutlined } from '@ant-design/icons';
import { api } from '../api';

const { TextArea } = Input;
const { Text } = Typography;

const suggestions = ['分析一下技术面', '当前估值如何', 'MACD 信号是什么', '支撑位和压力位在哪'];

export default function AgentPage() {
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState('分析一下技术面');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const chat = async () => {
    if (!code) { setError('请输入股票代码'); return; }
    setLoading(true); setError(''); setResponse('');
    try {
      const s = await api.createSession(code, code);
      const d = await api.agentChat(s.session_id, msg);
      setResponse(d.response);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ maxWidth: 800 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <Text strong style={{ fontSize: 20, color: '#1a1a2e', letterSpacing: '-0.3px' }}>AI 问股</Text>
          <Text type="secondary" style={{ display: 'block', fontSize: 13, marginTop: 2 }}>智能股票分析助手</Text>
        </div>
      </div>
      <Card className="glass-card" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <Input placeholder="股票代码 (例: 600519 / AAPL / 0700.HK)" value={code}
            onChange={e => setCode(e.target.value)} size="large" />
          <TextArea rows={3} placeholder="输入问题..." value={msg}
            onChange={e => setMsg(e.target.value)} style={{ resize: 'none' }} />
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {suggestions.map((s, i) => (
              <Tag key={s} className={`tag-pop`} style={{ cursor: 'pointer', borderRadius: 4, fontSize: 12, color: '#f5642a', background: 'rgba(245,100,42,0.06)', border: '1px solid rgba(245,100,42,0.15)' }}
                onClick={() => setMsg(s)}><BulbOutlined style={{ marginRight: 3 }} />{s}</Tag>
            ))}
          </div>
          <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={chat} size="large" block>
            💬 发送
          </Button>
        </Space>
      </Card>
      {error && <Alert type="error" message={error} showIcon style={{ marginBottom: 16 }} closable onClose={() => setError('')} />}
      {loading &&
        <Card className="glass-card" style={{ marginBottom: 16 }}>
          <div style={{ textAlign: 'center', padding: 20 }}>
            <div className="loading-breathe" style={{ marginBottom: 12 }}>
              <div className="dot-pulse" style={{ margin: '0 auto' }} />
            </div>
            <Text className="loading-text">AI 思考中...</Text>
          </div>
        </Card>
      }
      {response && (
        <Card className="glass-card" style={{ marginBottom: 16, animation: 'fade-in 0.4s ease' }}>
          <div style={{ marginBottom: 12 }}>
            <Space>
              <RobotOutlined style={{ color: '#1e88e5', fontSize: 16 }} />
              <Text strong style={{ color: '#1e88e5', fontSize: 14 }}>AI 分析</Text>
              {code && <Tag style={{ borderRadius: 4 }}>{code}</Tag>}
            </Space>
          </div>
          <div style={{
            background: 'rgba(30,136,229,0.04)', borderRadius: 8, padding: '12px 16px',
            borderLeft: '3px solid rgba(30,136,229,0.25)',
          }}>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7, fontFamily: 'inherit', color: '#475569', margin: 0 }}>
              {response}
            </pre>
          </div>
        </Card>
      )}
    </div>
  );
}
