import { useState } from 'react';
import { ConfigProvider, Layout, Menu, theme } from 'antd';
import {
  BarChartOutlined, LineChartOutlined, WalletOutlined,
  AlertOutlined, RobotOutlined, ExperimentOutlined, SettingOutlined,
} from '@ant-design/icons';
import AnalysisPage from './pages/AnalysisPage';
import MarketPage from './pages/MarketPage';
import PortfolioPage from './pages/PortfolioPage';
import AlertsPage from './pages/AlertsPage';
import AgentPage from './pages/AgentPage';
import BacktestPage from './pages/BacktestPage';
import ConfigPage from './pages/ConfigPage';

const { Header, Content, Sider } = Layout;

const menuItems = [
  { key: 'analysis', icon: <BarChartOutlined />, label: '分析' },
  { key: 'market', icon: <LineChartOutlined />, label: '大盘' },
  { key: 'portfolio', icon: <WalletOutlined />, label: '持仓' },
  { key: 'alerts', icon: <AlertOutlined />, label: '告警' },
  { key: 'agent', icon: <RobotOutlined />, label: '问股' },
  { key: 'backtest', icon: <ExperimentOutlined />, label: '回测' },
  { key: 'config', icon: <SettingOutlined />, label: '配置' },
];

const pages: Record<string, React.FC> = {
  analysis: AnalysisPage, market: MarketPage, portfolio: PortfolioPage,
  alerts: AlertsPage, agent: AgentPage, backtest: BacktestPage, config: ConfigPage,
};

export default function App() {
  const [page, setPage] = useState('analysis');
  const PageComponent = pages[page] || AnalysisPage;

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: { colorPrimary: '#00d4aa', colorBgContainer: '#1a2d3d' },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={200} style={{ background: '#0f1923' }}>
          <div style={{ padding: '20px 16px', color: '#00d4aa', fontSize: 18, fontWeight: 700 }}>
            📊 StockWatcher
          </div>
          <Menu
            mode="inline"
            selectedKeys={[page]}
            items={menuItems}
            onClick={({ key }) => setPage(key)}
            style={{ background: 'transparent', borderRight: 0 }}
          />
        </Sider>
        <Layout>
          <Content style={{ padding: 24, overflow: 'auto' }}>
            <PageComponent />
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}
