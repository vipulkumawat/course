import React, { useState } from 'react';
import { Layout, Menu, Card, Input, Button, Table, DatePicker, Select, Tag, Space, Row, Col, Statistic } from 'antd';
import { SearchOutlined, ApiOutlined, BarChartOutlined, UserOutlined } from '@ant-design/icons';
import SearchInterface from './components/SearchInterface';
import ApiDocumentation from './components/ApiDocumentation';
import Dashboard from './components/Dashboard';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Option } = Select;

function App() {
  const [selectedKey, setSelectedKey] = useState('search');

  const menuItems = [
    {
      key: 'search',
      icon: <SearchOutlined />,
      label: 'Log Search',
    },
    {
      key: 'api',
      icon: <ApiOutlined />,
      label: 'API Documentation',
    },
    {
      key: 'dashboard',
      icon: <BarChartOutlined />,
      label: 'Analytics',
    },
  ];

  const renderContent = () => {
    switch (selectedKey) {
      case 'search':
        return <SearchInterface />;
      case 'api':
        return <ApiDocumentation />;
      case 'dashboard':
        return <Dashboard />;
      default:
        return <SearchInterface />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="header" style={{ background: '#1890ff', padding: '0 24px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          Log Search API
        </div>
        <div style={{ float: 'right', color: 'white' }}>
          <UserOutlined /> Test User
        </div>
      </Header>
      <Layout>
        <Sider width={200} className="site-layout-background">
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
            onSelect={({ key }) => setSelectedKey(key)}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            className="site-layout-background"
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
            }}
          >
            {renderContent()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
