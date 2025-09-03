import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Dashboard from './components/Dashboard';
import ExperimentList from './components/ExperimentList';
import FeatureFlagManager from './components/FeatureFlagManager';
import Navigation from './components/Navigation';
import './App.css';

const { Header, Content, Sider } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={250} theme="light">
          <div className="logo" style={{ padding: '16px', fontSize: '18px', fontWeight: 'bold' }}>
            A/B Testing
          </div>
          <Navigation />
        </Sider>
        <Layout>
          <Header style={{ background: '#fff', padding: '0 24px' }}>
            <h2 style={{ margin: 0 }}>Feature Flag & Experiment Management</h2>
          </Header>
          <Content style={{ margin: '24px', background: '#fff', padding: '24px' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/experiments" element={<ExperimentList />} />
              <Route path="/feature-flags" element={<FeatureFlagManager />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
