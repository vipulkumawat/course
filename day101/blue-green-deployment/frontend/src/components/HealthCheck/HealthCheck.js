import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Progress, Tag, Table, Button } from 'antd';
import { ReloadOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const HealthCheck = () => {
  const [healthData, setHealthData] = useState(null);
  const [environments, setEnvironments] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHealthData();
    const interval = setInterval(fetchHealthData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchHealthData = async () => {
    setLoading(true);
    try {
      const [healthResponse, envResponse] = await Promise.all([
        axios.get(`${API_BASE}/health`),
        axios.get(`${API_BASE}/environments`)
      ]);
      
      setHealthData(healthResponse.data);
      setEnvironments(envResponse.data);
    } catch (error) {
      console.error('Failed to fetch health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColumns = () => [
    {
      title: 'Check Name',
      dataIndex: 'check_name',
      key: 'check_name',
      render: (text) => <strong>{text.replace('_', ' ').toUpperCase()}</strong>
    },
    {
      title: 'Status',
      dataIndex: 'passed',
      key: 'passed',
      render: (passed) => (
        <Tag
          icon={passed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          color={passed ? 'green' : 'red'}
        >
          {passed ? 'PASSED' : 'FAILED'}
        </Tag>
      )
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message'
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => new Date(timestamp).toLocaleTimeString()
    }
  ];

  const calculateHealthScore = (health) => {
    if (!health || !health.checks) return 0;
    const passed = health.checks.filter(check => check.passed).length;
    return Math.round((passed / health.checks.length) * 100);
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card 
            title="System Health Overview" 
            variant="borderless"
            extra={
              <Button 
                type="primary" 
                icon={<ReloadOutlined />} 
                onClick={fetchHealthData}
                loading={loading}
              >
                Refresh
              </Button>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Progress
                      type="circle"
                      percent={healthData ? calculateHealthScore(healthData) : 0}
                      status={healthData?.is_healthy ? 'success' : 'exception'}
                    />
                    <h3>Overall Health</h3>
                  </div>
                </Card>
              </Col>
              
              <Col span={8}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Progress
                      type="circle"
                      percent={environments.blue ? calculateHealthScore(environments.blue.health) : 0}
                      status={environments.blue?.health?.is_healthy ? 'success' : 'exception'}
                      strokeColor="#1890ff"
                    />
                    <h3>Blue Environment</h3>
                  </div>
                </Card>
              </Col>
              
              <Col span={8}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <Progress
                      type="circle"
                      percent={environments.green ? calculateHealthScore(environments.green.health) : 0}
                      status={environments.green?.health?.is_healthy ? 'success' : 'exception'}
                      strokeColor="#52c41a"
                    />
                    <h3>Green Environment</h3>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="Blue Environment Health Checks" variant="borderless">
            <Table
              dataSource={environments.blue?.health?.checks || []}
              columns={getHealthColumns()}
              pagination={false}
              size="small"
              rowKey="check_name"
            />
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Green Environment Health Checks" variant="borderless">
            <Table
              dataSource={environments.green?.health?.checks || []}
              columns={getHealthColumns()}
              pagination={false}
              size="small"
              rowKey="check_name"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default HealthCheck;
