import React, { useState, useEffect } from 'react';
import { Table, Card, Select, Button, Tag, Space, Tooltip } from 'antd';
import { ReloadOutlined, RollbackOutlined } from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';

const { Option } = Select;

const ConfigHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tenantId, setTenantId] = useState('tenant-001');

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    loadHistory();
  }, [tenantId]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/config/${tenantId}/history`);
      setHistory(response.data.data);
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value) => {
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'changed_at',
      key: 'changed_at',
      render: (timestamp) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss'),
      sorter: (a, b) => new Date(a.changed_at) - new Date(b.changed_at),
      defaultSortOrder: 'descend',
    },
    {
      title: 'Configuration Key',
      dataIndex: 'config_key',
      key: 'config_key',
      render: (key) => <Tag color="blue">{key}</Tag>,
    },
    {
      title: 'Old Value',
      dataIndex: 'old_value',
      key: 'old_value',
      render: (value) => (
        <Tooltip title={formatValue(value)}>
          <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {formatValue(value)}
          </div>
        </Tooltip>
      ),
    },
    {
      title: 'New Value',
      dataIndex: 'new_value',
      key: 'new_value',
      render: (value) => (
        <Tooltip title={formatValue(value)}>
          <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {formatValue(value)}
          </div>
        </Tooltip>
      ),
    },
    {
      title: 'Changed By',
      dataIndex: 'changed_by',
      key: 'changed_by',
      render: (user) => <Tag color="green">{user}</Tag>,
    },
    {
      title: 'Reason',
      dataIndex: 'change_reason',
      key: 'change_reason',
      render: (reason) => reason || '-',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <h2>Configuration History</h2>
          <Select
            value={tenantId}
            onChange={setTenantId}
            style={{ width: 200 }}
          >
            <Option value="tenant-001">Tenant 001</Option>
            <Option value="tenant-002">Tenant 002</Option>
            <Option value="tenant-003">Tenant 003</Option>
          </Select>
        </Space>
        
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadHistory} loading={loading}>
            Reload
          </Button>
          <Button icon={<RollbackOutlined />} onClick={() => window.location.href = '/'}>
            Back to Config
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={history}
          loading={loading}
          rowKey={(record) => `${record.changed_at}-${record.config_key}`}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
        />
      </Card>
    </div>
  );
};

export default ConfigHistory;
