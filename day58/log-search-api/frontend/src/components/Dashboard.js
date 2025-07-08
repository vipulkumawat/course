import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Progress } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, ApiOutlined, SearchOutlined } from '@ant-design/icons';

function Dashboard() {
  const [metrics, setMetrics] = useState({
    totalQueries: 1247,
    avgResponseTime: 89.5,
    cacheHitRate: 73.2,
    errorRate: 2.1
  });

  const topQueries = [
    { query: 'error payment', count: 45, trend: 'up' },
    { query: 'timeout database', count: 38, trend: 'down' },
    { query: 'login failed', count: 29, trend: 'up' },
    { query: 'api gateway', count: 24, trend: 'stable' },
    { query: 'memory usage', count: 19, trend: 'up' }
  ];

  const recentActivity = [
    {
      time: '10:30:15',
      user: 'admin',
      query: 'error payment timeout',
      results: 156,
      duration: '45ms'
    },
    {
      time: '10:29:45',
      user: 'developer',
      query: 'database connection',
      results: 23,
      duration: '67ms'
    },
    {
      time: '10:28:30',
      user: 'ops-team',
      query: 'memory leak',
      results: 8,
      duration: '123ms'
    }
  ];

  const queryColumns = [
    {
      title: 'Query',
      dataIndex: 'query',
      key: 'query',
      render: (text) => <span style={{ fontFamily: 'monospace' }}>{text}</span>
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      width: 80
    },
    {
      title: 'Trend',
      dataIndex: 'trend',
      key: 'trend',
      width: 80,
      render: (trend) => {
        const colors = { up: 'red', down: 'green', stable: 'gray' };
        const icons = { 
          up: <ArrowUpOutlined />, 
          down: <ArrowDownOutlined />, 
          stable: <span>-</span> 
        };
        return <span style={{ color: colors[trend] }}>{icons[trend]}</span>;
      }
    }
  ];

  const activityColumns = [
    {
      title: 'Time',
      dataIndex: 'time',
      key: 'time',
      width: 100
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      width: 120,
      render: (user) => <Tag color="blue">{user}</Tag>
    },
    {
      title: 'Query',
      dataIndex: 'query',
      key: 'query',
      ellipsis: true
    },
    {
      title: 'Results',
      dataIndex: 'results',
      key: 'results',
      width: 80
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      width: 80
    }
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Queries"
              value={metrics.totalQueries}
              prefix={<SearchOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={metrics.avgResponseTime}
              suffix="ms"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Cache Hit Rate"
              value={metrics.cacheHitRate}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Error Rate"
              value={metrics.errorRate}
              suffix="%"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Top Search Queries">
            <Table
              columns={queryColumns}
              dataSource={topQueries}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="API Performance">
            <div style={{ marginBottom: 16 }}>
              <div>Response Time Distribution</div>
              <Progress 
                percent={85} 
                strokeColor="#52c41a" 
                format={() => '< 100ms'}
                style={{ marginBottom: 8 }}
              />
              <Progress 
                percent={12} 
                strokeColor="#faad14" 
                format={() => '100-500ms'}
                style={{ marginBottom: 8 }}
              />
              <Progress 
                percent={3} 
                strokeColor="#f5222d" 
                format={() => '> 500ms'}
              />
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="Recent Search Activity">
        <Table
          columns={activityColumns}
          dataSource={recentActivity}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
}

export default Dashboard;
