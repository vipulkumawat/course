import React, { useState, useEffect } from 'react';
import { Card, Form, Input, InputNumber, Select, Button, Switch, message, Spin, Tag, Space } from 'antd';
import { SaveOutlined, ReloadOutlined, HistoryOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;
const { TextArea } = Input;

const TenantConfigDashboard = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState(null);
  const [tenantId, setTenantId] = useState('tenant-001');
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    loadConfig();
    setupWebSocket();
  }, [tenantId]);

  const setupWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/config/${tenantId}`);
    
    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'config_update') {
        message.info('Configuration updated in real-time');
        loadConfig(); // Reload config when changes occur
      }
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };
    
    return () => ws.close();
  };

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/config/${tenantId}`);
      const configData = response.data.data;
      setConfig(configData);
      form.setFieldsValue(configData);
      setLastUpdate(configData._updated_at);
    } catch (error) {
      message.error('Failed to load configuration');
      console.error('Load config error:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async (values) => {
    setLoading(true);
    try {
      // Remove internal fields
      const cleanValues = Object.fromEntries(
        Object.entries(values).filter(([key]) => !key.startsWith('_'))
      );
      
      await axios.put(`${API_BASE}/config/${tenantId}`, cleanValues);
      message.success('Configuration saved successfully');
      loadConfig(); // Reload to get updated timestamps
    } catch (error) {
      message.error(`Failed to save configuration: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetConfig = async () => {
    setLoading(true);
    try {
      await axios.delete(`${API_BASE}/config/${tenantId}`);
      message.success('Configuration reset to defaults');
      loadConfig();
    } catch (error) {
      message.error('Failed to reset configuration');
    } finally {
      setLoading(false);
    }
  };

  if (!config) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <h2>Tenant Configuration</h2>
          <Select
            value={tenantId}
            onChange={setTenantId}
            style={{ width: 200 }}
          >
            <Option value="tenant-001">Tenant 001</Option>
            <Option value="tenant-002">Tenant 002</Option>
            <Option value="tenant-003">Tenant 003</Option>
          </Select>
          <Tag color={connected ? 'green' : 'red'}>
            {connected ? 'Connected' : 'Disconnected'}
          </Tag>
        </Space>
        
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadConfig} loading={loading}>
            Reload
          </Button>
          <Button icon={<HistoryOutlined />} onClick={() => window.location.href = '/history'}>
            History
          </Button>
        </Space>
      </div>

      {lastUpdate && (
        <div style={{ marginBottom: 16, fontSize: '12px', color: '#666' }}>
          Last updated: {new Date(lastUpdate).toLocaleString()}
        </div>
      )}

      <Form
        form={form}
        layout="vertical"
        onFinish={saveConfig}
        initialValues={config}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <Card title="Log Management" style={{ height: 'fit-content' }}>
            <Form.Item
              label="Log Retention (Days)"
              name="log_retention_days"
              rules={[{ type: 'number', min: 1, max: 2555, message: 'Must be between 1 and 2555 days' }]}
            >
              <InputNumber min={1} max={2555} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="Max Log Rate (per second)"
              name="max_log_rate_per_second"
              rules={[{ type: 'number', min: 1, max: 100000, message: 'Must be between 1 and 100,000' }]}
            >
              <InputNumber min={1} max={100000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="Custom Parsing Rules"
              name="custom_parsing_rules"
            >
              <Select mode="tags" placeholder="Add parsing rules" style={{ width: '100%' }}>
                <Option value="^ERROR.*">Error Pattern</Option>
                <Option value="^WARN.*">Warning Pattern</Option>
              </Select>
            </Form.Item>
          </Card>

          <Card title="Alerts & Notifications" style={{ height: 'fit-content' }}>
            <Form.Item
              label="Alert Email"
              name="alert_email"
              rules={[{ type: 'email', message: 'Please enter a valid email' }]}
            >
              <Input />
            </Form.Item>

            <Form.Item label="Alert Thresholds">
              <Form.Item
                name={['alert_thresholds', 'error_rate']}
                label="Error Rate Threshold"
                style={{ marginBottom: 8 }}
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
              
              <Form.Item
                name={['alert_thresholds', 'latency_p99']}
                label="P99 Latency (ms)"
                style={{ marginBottom: 8 }}
              >
                <InputNumber min={0} max={10000} style={{ width: '100%' }} />
              </Form.Item>
              
              <Form.Item
                name={['alert_thresholds', 'memory_usage']}
                label="Memory Usage Threshold"
                style={{ marginBottom: 0 }}
              >
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Form.Item>

            <Form.Item
              label="Webhook Endpoints"
              name="webhook_endpoints"
            >
              <Select mode="tags" placeholder="Add webhook URLs" style={{ width: '100%' }} />
            </Form.Item>
          </Card>
        </div>

        <Card title="UI Preferences" style={{ marginTop: 20 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
            <Form.Item
              label="Theme"
              name={['ui_preferences', 'theme']}
            >
              <Select>
                <Option value="light">Light</Option>
                <Option value="dark">Dark</Option>
                <Option value="auto">Auto</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="Dashboard Refresh Rate (seconds)"
              name={['ui_preferences', 'dashboard_refresh_rate']}
            >
              <InputNumber min={5} max={300} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              label="Default Time Range"
              name={['ui_preferences', 'default_time_range']}
            >
              <Select>
                <Option value="5m">5 minutes</Option>
                <Option value="15m">15 minutes</Option>
                <Option value="1h">1 hour</Option>
                <Option value="24h">24 hours</Option>
              </Select>
            </Form.Item>
          </div>
        </Card>

        <div style={{ marginTop: 24, textAlign: 'right' }}>
          <Space>
            <Button danger onClick={resetConfig} loading={loading}>
              Reset to Defaults
            </Button>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
              Save Configuration
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );
};

export default TenantConfigDashboard;
