import logoImg from './assets/logo.png';
import { useState, useEffect } from 'react';
import { ConfigProvider, Layout, Menu, theme, Button, Typography } from 'antd';
import {
  BarChartOutlined, SearchOutlined, LineChartOutlined, WalletOutlined,
  AlertOutlined, RobotOutlined, ExperimentOutlined, SettingOutlined, CloseOutlined,
} from '@ant-design/icons';
import AgentPanel from './pages/AgentPanel';
import AnalysisPage from './pages/AnalysisPage';
import MarketPage from './pages/MarketPage';
import PortfolioPage from './pages/PortfolioPage';
import AlertsPage from './pages/AlertsPage';
import HomePage from './pages/HomePage';
import StockScreeningPage from './pages/StockScreeningPage';
import BacktestPage from './pages/BacktestPage';
import ConfigPage from './pages/ConfigPage';

const { Content, Sider } = Layout;
const { Text } = Typography;

const menuItems = [
  { key: 'home', icon: <BarChartOutlined />, label: '首页' },
  { key: 'screening', icon: <SearchOutlined />, label: '选股' },
  { key: 'analysis', icon: <BarChartOutlined />, label: '分析' },
  { key: 'market', icon: <LineChartOutlined />, label: '大盘' },
  { key: 'portfolio', icon: <WalletOutlined />, label: '持仓' },
  { key: 'alerts', icon: <AlertOutlined />, label: '告警' },
  { key: 'backtest', icon: <ExperimentOutlined />, label: '回测' },
  { key: 'config', icon: <SettingOutlined />, label: '配置' },
];

const pages: Record<string, React.FC> = {
  home: HomePage, screening: StockScreeningPage,
  analysis: AnalysisPage, market: MarketPage, portfolio: PortfolioPage,
  alerts: AlertsPage, backtest: BacktestPage, config: ConfigPage,
};

function AppInner() {
  const [page, setPage] = useState('home');
  const [agentOpen, setAgentOpen] = useState(true);
  const [agentWidth, setAgentWidth] = useState(400);
  // keep-alive：记录访问过的页面，首次访问才挂载，之后保留在 DOM（隐藏），切回不重新请求
  const [visited, setVisited] = useState<Set<string>>(() => new Set(['home']));

  const navigate = (key: string) => {
    setVisited(prev => (prev.has(key) ? prev : new Set(prev).add(key)));
    setPage(key);
  };

  // 允许任意页面通过事件跳转（如配置页「去配置」跳到持仓页）
  useEffect(() => {
    const handler = (e: Event) => {
      const key = (e as CustomEvent<string>).detail;
      setVisited(prev => (prev.has(key) ? prev : new Set(prev).add(key)));
      setPage(key);
    };
    window.addEventListener('sw-navigate', handler);
    return () => window.removeEventListener('sw-navigate', handler);
  }, []);

  return (
    <Layout style={{ minHeight: '100vh', minWidth: 0, background: '#ffffff', position: 'relative', overflow: 'hidden' }}>
      {/* Full-screen watermark background */}
      <div style={{
        position: 'fixed',
        top: 0, left: 0,
        width: '100vw',
        height: '100vh',
        backgroundImage: `url(${logoImg})`,
        backgroundSize: '900px auto',
        backgroundRepeat: 'no-repeat',
        backgroundPosition: 'center center',
        opacity: 0.1,
        pointerEvents: 'none',
        zIndex: 0,
      }} />
      {/* Sider */}
      <Sider width={200} style={{
        background: '#fafafa',
        borderRight: '1px solid rgba(0,0,0,0.06)',
        position: 'relative',
        zIndex: 10,
      }}>
        {/* Logo */}
        <div style={{
          padding: '22px 20px 18px',
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          marginBottom: 4,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img
              src={logoImg}
              alt="logo"
              style={{
                width: 30, height: 30, borderRadius: 8,
                objectFit: 'cover', flexShrink: 0,
                boxShadow: '0 2px 8px rgba(245,100,42,0.25)',
              }}
            />
            <Text strong style={{ color: '#1a1a2e', fontSize: 17, letterSpacing: '-0.3px' }}>
              StockWatcher
            </Text>
          </div>
        </div>

        {/* Menu */}
        <Menu
          mode="inline"
          selectedKeys={[page]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: 'transparent', borderRight: 0,
            fontSize: 14, padding: '4px 0',
            color: '#64748b',
          }}
        />


      </Sider>

      {/* Content */}
      <Layout style={{ background: 'transparent' }}>
        <Content style={{
          padding: 24, overflow: 'auto', minHeight: '100vh',
          background: '#ffffff',
        }}>
          {/* keep-alive：只渲染访问过的页面；非当前页用 display:none 隐藏，保留状态、切回不重拉 */}
          {menuItems.map(item => {
            if (!visited.has(item.key)) return null;
            const Comp = pages[item.key] || AnalysisPage;
            return (
              <div key={item.key} style={{ display: page === item.key ? '' : 'none' }}>
                <Comp />
              </div>
            );
          })}
        </Content>
      </Layout>

      {/* Agent toggle button — fixed on the right edge */}
      <div onClick={() => setAgentOpen(!agentOpen)} style={{
        position: 'fixed',
        right: agentOpen ? Math.max(agentWidth, 320) : 0,
        top: '50%',
        transform: 'translateY(-50%)',
        width: 32,
        height: 120,
        background: 'linear-gradient(180deg, #f5642a, #ff8552)',
        borderRadius: '14px 0 0 14px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 4,
        cursor: 'pointer',
        zIndex: 1001,
        boxShadow: agentOpen
          ? '-2px 0 12px rgba(245,100,42,0.35), 0 4px 20px rgba(245,100,42,0.15)'
          : '2px 0 12px rgba(245,100,42,0.3), 0 4px 20px rgba(245,100,42,0.12)',
        transition: 'right 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease',
        userSelect: 'none',
      }}>
        <span style={{ color: '#fff', fontSize: 14, fontWeight: 600, writingMode: 'vertical-rl', letterSpacing: 2 }}>
          {agentOpen ? '收起' : '问股'}
        </span>
      </div>

      {/* Agent panel — fixed right drawer */}
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: agentOpen ? agentWidth : 0,
        minWidth: agentOpen ? 320 : 0,
        maxWidth: 600,
        transform: agentOpen ? 'translateX(0)' : 'translateX(100%)',
        transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        background: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        zIndex: 1000,
        borderLeft: '1px solid rgba(0,0,0,0.08)',
        boxShadow: agentOpen ? '-8px 0 32px rgba(0,0,0,0.08)' : 'none',
      }}>
        {/* Resize handle */}
        <div
          style={{
            position: 'absolute',
            left: -3,
            top: 0,
            bottom: 0,
            width: 6,
            cursor: 'col-resize',
            zIndex: 10,
          }}
          onMouseDown={(e) => {
            const startX = e.clientX;
            const startW = agentWidth;
            const onMove = (ev: MouseEvent) => {
              const newW = startW - (ev.clientX - startX);
              if (newW >= 320 && newW <= 600) setAgentWidth(newW);
            };
            const onUp = () => {
              document.removeEventListener('mousemove', onMove);
              document.removeEventListener('mouseup', onUp);
            };
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
          }}
        />

        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderBottom: '1px solid rgba(0,0,0,0.06)',
          flexShrink: 0,
          background: '#ffffff',
        }}>
          <span style={{ fontWeight: 600, color: '#1a1a2e', fontSize: 15 }}>
            <RobotOutlined style={{ marginRight: 8, color: '#f5642a' }} />问股
          </span>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={() => setAgentOpen(false)}
          />
        </div>
        {agentOpen && <AgentPanel />}
      </div>
    </Layout>
  );
}

export default function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: '#f5642a',
          colorBgContainer: '#ffffff',
          colorBgElevated: '#fafafa',
          colorBorderSecondary: 'rgba(0,0,0,0.06)',
          colorText: '#1a1a2e',
          colorTextSecondary: '#64748b',
          colorTextTertiary: '#94a3b8',
          borderRadius: 10,
          fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
        },
      }}
    >
      <AppInner />
    </ConfigProvider>
  );
}
