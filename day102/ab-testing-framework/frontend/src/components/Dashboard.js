import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Alert } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { ExperimentOutlined, FlagOutlined, UserOutlined, TrophyOutlined } from '@ant-design/icons';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    activeExperiments: 5,
    totalUsers: 12543,
    conversionRate: 14.5,
    significantResults: 3
  });

  const [experimentData] = useState([
    { name: 'Week 1', control: 12.3, treatment: 14.1 },
    { name: 'Week 2', control: 11.8, treatment: 15.2 },
    { name: 'Week 3', control: 12.1, treatment: 16.3 },
    { name: 'Week 4', control: 12.5, treatment: 15.8 }
  ]);

  const [flagUsage] = useState([
    { name: 'new-dashboard', usage: 85 },
    { name: 'enhanced-search', usage: 62 },
    { name: 'social-login', usage: 34 },
    { name: 'dark-mode', usage: 91 }
  ]);

  return (
    <div>
      <Alert
        message="A/B Testing Framework Active"
        description="All experiments are running normally. 3 experiments show significant results."
        type="success"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Experiments"
              value={metrics.activeExperiments}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Users in Experiments"
              value={metrics.totalUsers}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Conversion Rate"
              value={metrics.conversionRate}
              precision={1}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Significant Results"
              value={metrics.significantResults}
              prefix={<FlagOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="Experiment Performance Trends" style={{ marginBottom: 16 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={experimentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="control" stroke="#1890ff" name="Control" />
                <Line type="monotone" dataKey="treatment" stroke="#52c41a" name="Treatment" />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card title="Feature Flag Usage">
            {flagUsage.map(flag => (
              <div key={flag.name} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>{flag.name}</span>
                  <span>{flag.usage}%</span>
                </div>
                <Progress percent={flag.usage} showInfo={false} />
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
