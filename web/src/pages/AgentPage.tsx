import { useState } from 'react';
import { Card, Input, Button, Alert, Typography, Space, Select } from 'antd';
import { SendOutlined, RobotOutlined } from '@ant-design/icons';
import { api } from '../api';

const { TextArea } = Input;
const { Text } = Typography;

export default function AgentPage() {
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState('分析一下技术面');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [strategies, setStrategies] = useState<Record<string, string>>({});

  const start = async () => {
    if (!code) return;
    setLoading(true); setError(''); setResponse('');
    try {
      const s = await api.createSession(code, code);
      const d = await api.agentChat(s.session_id, msg);
      setResponse(d.response);
    } catch (e: any) {
      setError(e.message);
    } finally { setLoading(false); }
  };

  const chat = async () => {
    if (!code) return;
    setLoading(true); setError('');
    try {
      const s = await api.createSession(code, code);
      const d = await api.agentChat(s.session_id, msg);
      setResponse(d.response);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Card>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input placeholder="股票代码" value={code} onChange={e => setCode(e.target.value)} />
          <TextArea rows={2} placeholder="输入问题..." value={msg} onChange={e => setMsg(e.target.value)} />
          <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={chat}>
            💬 问股
          </Button>
        </Space>
      </Card>
      {error && <Alert type="error" message={error} showIcon style={{ marginTop: 16 }} />}
      {response && (
        <Card title={<><RobotOutlined /> AI 分析: {code}</>} style={{ marginTop: 16 }}>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7 }}>{response}</pre>
        </Card>
      )}
    </div>
  );
}
