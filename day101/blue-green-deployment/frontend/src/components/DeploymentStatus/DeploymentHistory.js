import React, { useState, useEffect } from 'react';
import { Card, Table, Tag, Timeline, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

const DeploymentHistory = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/history`);
      setHistory(response.data.deployments || []);
    } catch (error) {
      console.error('Failed to fetch deployment history:', error);
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

  const columns = [
    {
      title: 'Deployment ID',
      dataIndex: 'deployment_id',
      key: 'deployment_id',
      ellipsis: true
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version'
    },
    {
      title: 'State',
      dataIndex: 'state',
      key: 'state',
      render: (state) => (
        <Tag color={getStateColor(state)}>
          {state.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Environment',
      dataIndex: 'active_environment',
      key: 'active_environment',
      render: (env) => (
        <Tag color={env === 'blue' ? 'blue' : 'green'}>
          {env.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => new Date(timestamp).toLocaleString()
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    }
  ];

  const timelineItems = history.map((deployment, index) => ({
    color: getStateColor(deployment.state),
    children: (
      <div key={index}>
        <strong>{deployment.version}</strong> - {deployment.state}
        <br />
        <small>{new Date(deployment.timestamp).toLocaleString()}</small>
        <br />
        <small>{deployment.message}</small>
      </div>
    )
  }));

  return (
    <div>
      <Card 
        title="Deployment History" 
        variant="borderless"
        extra={
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={fetchHistory}
            loading={loading}
          >
            Refresh
          </Button>
        }
      >
        <Table
          dataSource={history}
          columns={columns}
          pagination={{ pageSize: 10 }}
          loading={loading}
          rowKey="deployment_id"
        />
      </Card>

              <Card title="Deployment Timeline" variant="borderless" style={{ marginTop: 16 }}>
        <Timeline items={timelineItems} />
      </Card>
    </div>
  );
};

export default DeploymentHistory;
