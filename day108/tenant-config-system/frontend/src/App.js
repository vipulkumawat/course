import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Layout, Menu } from 'antd';
import { HomeOutlined, HistoryOutlined } from '@ant-design/icons';
import TenantConfigDashboard from './components/TenantConfigDashboard';
import ConfigHistory from './components/ConfigHistory';
import './App.css';

const { Header, Content, Sider } = Layout;
const queryClient = new QueryClient();

function NavigationMenu() {
  const location = useLocation();
  
  const menuItems = [
    {
      key: '1',
      icon: <HomeOutlined />,
      label: <Link to="/">Configuration</Link>,
    },
    {
      key: '2',
      icon: <HistoryOutlined />,
      label: <Link to="/history">History</Link>,
    },
  ];

  return (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname === '/' ? '1' : '2']}
      items={menuItems}
      style={{ height: '100%', borderRight: 0 }}
    />
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <Layout style={{ minHeight: '100vh' }}>
          <Header className="header">
            <div className="logo">Tenant Configuration Dashboard</div>
          </Header>
          <Layout>
            <Sider width={200} className="site-layout-background">
              <NavigationMenu />
            </Sider>
            <Layout style={{ padding: '0 24px 24px' }}>
              <Content
                className="site-layout-background"
                style={{
                  padding: 24,
                  margin: 0,
                  minHeight: 280,
                }}
              >
                <Routes>
                  <Route path="/" element={<TenantConfigDashboard />} />
                  <Route path="/history" element={<ConfigHistory />} />
                </Routes>
              </Content>
            </Layout>
          </Layout>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
