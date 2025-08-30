import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Modal, Form, Input, Switch, Tag, Alert } from 'antd';
import { DeploymentUnitOutlined, SwapOutlined, RollbackOutlined } from '@ant-design/icons';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const Dashboard = () => {
  const [deploymentStatus, setDeploymentStatus] = useState(null);
  const [environments, setEnvironments] = useState({});
  const [deployModalVisible, setDeployModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [websocket, setWebsocket] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Initial data load
    const fetchInitialData = async () => {
      try {
        const [statusResponse, envResponse] = await Promise.all([
          axios.get(`${API_BASE}/status`),
          axios.get(`${API_BASE}/environments`)
        ]);
        setDeploymentStatus(statusResponse.data);
        setEnvironments(envResponse.data);
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
      }
    };

    fetchInitialData();

    // Setup WebSocket connection
    const newWebsocket = new WebSocket('ws://localhost:8000/ws');
    newWebsocket.onopen = () => {
      console.log('Connected to WebSocket');
      setWsConnected(true);
    };

    newWebsocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setDeploymentStatus(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    newWebsocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    newWebsocket.onclose = () => {
      console.log('WebSocket connection closed');
      setWsConnected(false);
    };

    setWebsocket(newWebsocket);

    // Cleanup
    return () => {
      if (newWebsocket && newWebsocket.readyState === WebSocket.OPEN) {
        newWebsocket.close();
      }
    };
  }, []);



  const fetchDeploymentStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/status`);
      setDeploymentStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch deployment status:', error);
    }
  };

  const fetchEnvironments = async () => {
    try {
      const response = await axios.get(`${API_BASE}/environments`);
      setEnvironments(response.data);
    } catch (error) {
      console.error('Failed to fetch environments:', error);
    }
  };

  const handleDeploy = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/deploy`, {
        version: values.version,
        config: {
          new_feature: values.new_feature || false
        }
      });
      
      setDeploymentStatus(response.data);
      setDeployModalVisible(false);
      
      // Refresh environments
      setTimeout(() => {
        fetchEnvironments();
      }, 2000);
      
    } catch (error) {
      console.error('Deployment failed:', error);
      alert('Deployment failed: ' + error.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/rollback`);
      fetchDeploymentStatus();
      fetchEnvironments();
    } catch (error) {
      console.error('Rollback failed:', error);
      alert('Rollback failed: ' + error.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const getStateColor = (state) => {
    const colors = {
      stable: 'green',
      deploying: 'blue',
      completed: 'green',
      failed: 'red',
      rolling_back: 'orange'
    };
    return colors[state] || 'default';
  };

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Alert
            message="Zero-Downtime Deployment System"
            description="Monitor and control blue/green deployments for your distributed log processing system"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="Current Status" variant="borderless">
            {deploymentStatus ? (
              <div>
                <p><strong>State:</strong> <Tag color={getStateColor(deploymentStatus.state)}>{deploymentStatus.state}</Tag></p>
                <p><strong>Active Environment:</strong> <Tag color={deploymentStatus.active_environment === 'blue' ? 'blue' : 'green'}>{deploymentStatus.active_environment}</Tag></p>
                <p><strong>Version:</strong> {deploymentStatus.version}</p>
                <p><strong>Last Update:</strong> {new Date(deploymentStatus.timestamp).toLocaleString()}</p>
              </div>
            ) : (
              <p>Loading...</p>
            )}
          </Card>
        </Col>

        <Col span={8}>
          <Card title="Blue Environment" variant="borderless">
            {environments.blue ? (
              <div>
                <p><strong>Port:</strong> {environments.blue.port}</p>
                <p><strong>Status:</strong> 
                  <Tag color={environments.blue.health?.is_healthy ? 'green' : 'red'}>
                    {environments.blue.health?.is_healthy ? 'Healthy' : 'Unhealthy'}
                  </Tag>
                </p>
                <p><strong>Active:</strong> 
                  <Tag color={environments.blue.active ? 'green' : 'default'}>
                    {environments.blue.active ? 'Active' : 'Standby'}
                  </Tag>
                </p>
              </div>
            ) : (
              <p>Loading...</p>
            )}
          </Card>
        </Col>

        <Col span={8}>
          <Card title="Green Environment" variant="borderless">
            {environments.green ? (
              <div>
                <p><strong>Port:</strong> {environments.green.port}</p>
                <p><strong>Status:</strong> 
                  <Tag color={environments.green.health?.is_healthy ? 'green' : 'red'}>
                    {environments.green.health?.is_healthy ? 'Healthy' : 'Unhealthy'}
                  </Tag>
                </p>
                <p><strong>Active:</strong> 
                  <Tag color={environments.green.active ? 'green' : 'default'}>
                    {environments.green.active ? 'Active' : 'Standby'}
                  </Tag>
                </p>
              </div>
            ) : (
              <p>Loading...</p>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Actions" variant="borderless">
            <Button
              type="primary"
              icon={<DeploymentUnitOutlined />}
              onClick={() => setDeployModalVisible(true)}
              loading={loading}
              style={{ marginRight: 8 }}
            >
              Deploy New Version
            </Button>
            <Button
              type="default"
              icon={<RollbackOutlined />}
              onClick={handleRollback}
              loading={loading}
              danger
            >
              Emergency Rollback
            </Button>
          </Card>
        </Col>
      </Row>

      <Modal
        title="Deploy New Version"
        open={deployModalVisible}
        onCancel={() => setDeployModalVisible(false)}
        footer={null}
      >
        <Form onFinish={handleDeploy} layout="vertical">
          <Form.Item
            name="version"
            label="Version"
            rules={[{ required: true, message: 'Please enter version!' }]}
          >
            <Input placeholder="e.g., v2.1.0" />
          </Form.Item>
          
          <Form.Item
            name="new_feature"
            label="Enable New Feature"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              Deploy
            </Button>
            <Button onClick={() => setDeployModalVisible(false)} style={{ marginLeft: 8 }}>
              Cancel
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
