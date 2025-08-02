import React, { useState, useEffect } from 'react';
import { Layout, Card, Row, Col, Statistic, Table, Tag, Timeline, Spin } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import axios from 'axios';
import moment from 'moment';
import './App.css';

const { Header, Content } = Layout;

function App() {
  const [correlations, setCorrelations] = useState([]);
  const [stats, setStats] = useState({});
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [correlationsRes, statsRes, logsRes] = await Promise.all([
        axios.get('/api/v1/correlations?limit=50'),
        axios.get('/api/v1/correlations/stats'),
        axios.get('/api/v1/logs/recent?count=20')
      ]);

      setCorrelations(correlationsRes.data.correlations);
      setStats(statsRes.data);
      setRecentLogs(logsRes.data.events);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const getCorrelationTypeColor = (type) => {
    const colors = {
      'session_based': 'blue',
      'user_based': 'green',
      'error_cascade': 'red',
      'metric_based': 'orange'
    };
    return colors[type] || 'default';
  };

  const getLevelColor = (level) => {
    const colors = {
      'INFO': 'green',
      'WARN': 'orange',
      'ERROR': 'red'
    };
    return colors[level] || 'default';
  };

  const correlationColumns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => moment(timestamp).format('HH:mm:ss'),
      width: 80,
    },
    {
      title: 'Type',
      dataIndex: 'correlation_type',
      key: 'correlation_type',
      render: (type) => <Tag color={getCorrelationTypeColor(type)}>{type.replace('_', ' ')}</Tag>,
      width: 120,
    },
    {
      title: 'Strength',
      dataIndex: 'strength',
      key: 'strength',
      render: (strength) => (
        <div>
          <div style={{ width: '100px', height: '10px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
            <div 
              style={{ 
                width: `${strength * 100}%`, 
                height: '100%', 
                backgroundColor: strength > 0.7 ? '#52c41a' : strength > 0.4 ? '#faad14' : '#ff4d4f',
                borderRadius: '5px'
              }}
            />
          </div>
          <span style={{ fontSize: '12px' }}>{(strength * 100).toFixed(1)}%</span>
        </div>
      ),
      width: 120,
    },
    {
      title: 'Source A',
      key: 'source_a',
      render: (record) => (
        <div>
          <div><strong>{record.event_a.source}</strong> ({record.event_a.service})</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.event_a.message}</div>
        </div>
      ),
    },
    {
      title: 'Source B',
      key: 'source_b',
      render: (record) => (
        <div>
          <div><strong>{record.event_b.source}</strong> ({record.event_b.service})</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.event_b.message}</div>
        </div>
      ),
    },
  ];

  const logColumns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => moment(timestamp).format('HH:mm:ss'),
      width: 80,
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      width: 80,
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      render: (level) => <Tag color={getLevelColor(level)}>{level}</Tag>,
      width: 80,
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: 'User ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 100,
    },
  ];

  // Prepare chart data
  const correlationTimeData = correlations.map((corr, index) => ({
    time: moment(corr.timestamp).format('HH:mm:ss'),
    strength: corr.strength * 100,
    type: corr.correlation_type,
    index
  })).slice(-20);

  const correlationScatterData = correlations.map((corr, index) => ({
    x: moment(corr.timestamp).valueOf(),
    y: corr.strength * 100,
    type: corr.correlation_type,
    confidence: corr.confidence * 100
  })).slice(-50);

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ background: '#001529', color: 'white', textAlign: 'center' }}>
          <h1 style={{ color: 'white', margin: 0 }}>Correlation Analysis System</h1>
        </Header>
        <Content style={{ padding: '50px', textAlign: 'center' }}>
          <Spin size="large" />
          <p style={{ marginTop: '20px' }}>Loading correlation analysis...</p>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', color: 'white', textAlign: 'center' }}>
        <h1 style={{ color: 'white', margin: 0 }}>🔗 Correlation Analysis System</h1>
      </Header>
      
      <Content style={{ padding: '24px' }}>
        {/* Statistics Cards */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Total Correlations" 
                value={stats.total || 0} 
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Average Strength" 
                value={(stats.avg_strength * 100 || 0).toFixed(1)} 
                suffix="%" 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Recent (5 min)" 
                value={stats.recent_count || 0} 
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Max Strength" 
                value={(stats.max_strength * 100 || 0).toFixed(1)} 
                suffix="%" 
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Charts */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={12}>
            <Card title="Correlation Strength Over Time" size="small">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={correlationTimeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Strength']} />
                  <Line type="monotone" dataKey="strength" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          <Col span={12}>
            <Card title="Correlation Distribution" size="small">
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart data={correlationScatterData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" scale="time" dataKey="x" domain={['dataMin', 'dataMax']} tickFormatter={(value) => moment(value).format('HH:mm')} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip formatter={(value, name) => name === 'y' ? [`${value.toFixed(1)}%`, 'Strength'] : [value, name]} />
                  <Scatter dataKey="y" fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* Tables */}
        <Row gutter={16}>
          <Col span={14}>
            <Card title="Recent Correlations" size="small">
              <Table 
                dataSource={correlations.slice(0, 10)} 
                columns={correlationColumns}
                pagination={false}
                size="small"
                rowKey={(record, index) => index}
              />
            </Card>
          </Col>
          <Col span={10}>
            <Card title="Recent Log Events" size="small">
              <Table 
                dataSource={recentLogs} 
                columns={logColumns}
                pagination={false}
                size="small"
                rowKey={(record, index) => index}
              />
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
}

export default App;
