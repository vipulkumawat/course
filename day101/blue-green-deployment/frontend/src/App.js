import React, { useState, useEffect } from 'react';
import { Layout, Menu } from 'antd';
import { DashboardOutlined, HeartOutlined, HistoryOutlined } from '@ant-design/icons';
import Dashboard from './components/Dashboard/Dashboard';
import HealthCheck from './components/HealthCheck/HealthCheck';
import DeploymentHistory from './components/DeploymentStatus/DeploymentHistory';
import './App.css';

const { Header, Sider, Content } = Layout;

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: 'health',
      icon: <HeartOutlined />,
      label: 'Health Status',
    },
    {
      key: 'history',
      icon: <HistoryOutlined />,
      label: 'Deployment History',
    },
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'health':
        return <HealthCheck />;
      case 'history':
        return <DeploymentHistory />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div className="logo">
          <h3 style={{ color: 'white', textAlign: 'center', padding: '16px' }}>
            {collapsed ? 'B/G' : 'Blue/Green'}
          </h3>
        </div>
        <Menu
          theme="dark"
          selectedKeys={[currentView]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => setCurrentView(key)}
        />
      </Sider>
      <Layout className="site-layout">
        <Header className="site-layout-background" style={{ padding: 0, background: '#fff' }}>
          <h2 style={{ margin: '0 24px', lineHeight: '64px' }}>
            Blue/Green Deployment Controller
          </h2>
        </Header>
        <Content
          className="site-layout-background"
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: '#fff'
          }}
        >
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
