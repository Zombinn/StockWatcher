import { useState, useRef, useEffect } from 'react';
import { Input, Button, Spin, Typography, Tag, Alert, Space } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ClearOutlined, BulbOutlined } from '@ant-design/icons';
import { api } from '../api';

const { Text } = Typography;

interface Message {
  role: 'user' | 'assistant';
  content: string;
  code?: string;
}

const stockTags = ['AAPL', 'TSLA', '000001', '600519', '0700.HK'];
const quickQuestions = ['技术面分析', 'MACD 信号', '估值如何', '支撑压力'];

export default function AgentPanel() {
  const [code, setCode] = useState('AAPL');
  const [input, setInput] = useState('分析一下技术面');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const chat = async () => {
    if (!code) { setError('请输入股票代码'); return; }
    const trimmed = input.trim();
    if (!trimmed) return;

    setError('');
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: trimmed, code }]);
    setLoading(true);
    try {
      let sid = sessionId;
      if (!sid) {
        const s = await api.createSession(code, code) as any;
        sid = s.session_id;
        setSessionId(sid);
      }
      const d = await api.agentChat(sid!, trimmed);
      setMessages(prev => [...prev, { role: 'assistant', content: d.response }]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const newSession = () => {
    setSessionId(null);
    setMessages([]);
    setError('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Messages area */}
      <div ref={listRef} style={{
        flex: 1, overflowY: 'auto', padding: '16px 18px',
        display: 'flex', flexDirection: 'column', gap: 14,
        minHeight: 0,
      }}>
        {messages.length === 0 && !loading && (
          <div style={{ textAlign: 'center', paddingTop: 40, color: '#94a3b8' }}>
            <RobotOutlined style={{ fontSize: 32, display: 'block', marginBottom: 8, opacity: 0.35 }} />
            <Text type="secondary" style={{ fontSize: 13 }}>选择股票开始提问</Text>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className="fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
              {m.role === 'user' ? (
                <>
                  <div style={{
                    width: 28, height: 28, borderRadius: 7,
                    background: 'rgba(245,100,42,0.12)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14,
                  }}>
                    <UserOutlined style={{ color: '#f5642a', fontSize: 13 }} />
                  </div>
                  <Text strong style={{ color: '#f5642a', fontSize: 14 }}>你</Text>
                  {m.code && <Tag style={{ fontSize: 12, lineHeight: '20px', borderRadius: 4, padding: '0 8px' }}>{m.code}</Tag>}
                </>
              ) : (
                <>
                  <div style={{
                    width: 28, height: 28, borderRadius: 7,
                    background: 'rgba(30,136,229,0.12)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14,
                  }}>
                    <RobotOutlined style={{ color: '#1e88e5', fontSize: 13 }} />
                  </div>
                  <Text strong style={{ color: '#1e88e5', fontSize: 14 }}>AI</Text>
                </>
              )}
            </div>
            <div style={{
              background: m.role === 'user' ? 'rgba(245,100,42,0.04)' : 'rgba(30,136,229,0.03)',
              borderRadius: 10, padding: '10px 14px', marginLeft: 28, fontSize: 14,
              borderLeft: m.role === 'assistant' ? '3px solid rgba(30,136,229,0.18)' : 'none',
            }}>
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7, fontFamily: 'inherit', color: '#475569' }}>
                {m.content}
              </pre>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingLeft: 28 }}>
            <Spin size="small" />
            <Text className="loading-text" style={{ fontSize: 12 }}>AI 思考中...</Text>
          </div>
        )}
      </div>

      {error && (
        <Alert type="error" message={error} showIcon closable onClose={() => setError('')}
          style={{ margin: '0 18px 8px', fontSize: 13, borderRadius: 8 }} />
      )}

      {/* Input area */}
      <div style={{
        borderTop: '1px solid rgba(0,0,0,0.06)',
        padding: '12px 18px 18px',
        display: 'flex', flexDirection: 'column', gap: 10,
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
          {stockTags.map(s => (
            <Tag key={s} color={code === s ? 'orange' : 'default'}
              style={{ cursor: 'pointer', fontSize: 13, lineHeight: '24px', padding: '0 10px', margin: 0, borderRadius: 4 }}
              onClick={() => setCode(s)}>{s}</Tag>
          ))}
          <Input placeholder="代码" size="small" value={code}
            onChange={e => setCode(e.target.value)}
            style={{ width: 100, height: 32, fontSize: 14, borderRadius: 6 }} />
        </div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {quickQuestions.map(q => (
            <Tag key={q} style={{ cursor: 'pointer', fontSize: 12, lineHeight: '22px', borderRadius: 4, margin: 0, padding: '0 8px', color: '#f5642a', background: 'rgba(245,100,42,0.06)', border: '1px solid rgba(245,100,42,0.12)' }}
              icon={<BulbOutlined />} onClick={() => setInput(q)}>{q}</Tag>
          ))}
        </div>
        <Input.TextArea rows={4} placeholder="输入问题..."
          value={input} onChange={e => setInput(e.target.value)}
          onPressEnter={e => { if (!e.shiftKey) { e.preventDefault(); chat(); }}}
          style={{ resize: 'none', fontSize: 14, borderRadius: 8, padding: '10px 12px' }} />
        <div style={{ display: 'flex', gap: 6 }}>
          <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={chat}
            style={{ flex: 1, borderRadius: 8, fontSize: 14, height: 40 }}>
            发送
          </Button>
          <Button icon={<ClearOutlined />} onClick={newSession}
            style={{ borderRadius: 8, fontSize: 14, height: 40 }}>
            新会话
          </Button>
        </div>
      </div>
    </div>
  );
}
