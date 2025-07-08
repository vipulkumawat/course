import React from 'react';
import { Card, Typography, Divider, Tag, Table, Button, Space } from 'antd';
import { CopyOutlined, LinkOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

function ApiDocumentation() {
  const endpoints = [
    {
      method: 'POST',
      path: '/api/v1/logs/search',
      description: 'Advanced search with request body',
      status: 'Active'
    },
    {
      method: 'GET', 
      path: '/api/v1/logs/search',
      description: 'Simple search with query parameters',
      status: 'Active'
    },
    {
      method: 'GET',
      path: '/api/v1/logs/suggest',
      description: 'Get query suggestions',
      status: 'Active'
    },
    {
      method: 'GET',
      path: '/api/v1/logs/metrics',
      description: 'Get search analytics',
      status: 'Active'
    }
  ];

  const columns = [
    {
      title: 'Method',
      dataIndex: 'method',
      key: 'method',
      render: (method) => {
        const colors = { GET: 'green', POST: 'blue', PUT: 'orange', DELETE: 'red' };
        return <Tag color={colors[method]}>{method}</Tag>;
      }
    },
    {
      title: 'Endpoint',
      dataIndex: 'path',
      key: 'path',
      render: (path) => <Text code>{path}</Text>
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color="green">{status}</Tag>
    }
  ];

  return (
    <div>
      <Card>
        <Title level={2}>Log Search API Documentation</Title>
        <Paragraph>
          RESTful API for querying distributed log data with advanced search capabilities,
          relevance scoring, and real-time filtering.
        </Paragraph>

        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<LinkOutlined />}>
            Interactive Docs
          </Button>
          <Button icon={<CopyOutlined />}>
            Copy API Key
          </Button>
        </Space>

        <Divider />

        <Title level={3}>Authentication</Title>
        <Paragraph>
          All API requests require authentication using Bearer tokens in the Authorization header:
        </Paragraph>
        <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px', marginBottom: '16px' }}>
          <Text code>Authorization: Bearer YOUR_ACCESS_TOKEN</Text>
        </div>

        <Title level={3}>Available Endpoints</Title>
        <Table
          columns={columns}
          dataSource={endpoints}
          pagination={false}
          style={{ marginBottom: 24 }}
        />

        <Title level={3}>Example Requests</Title>
        
        <Card size="small" title="POST /api/v1/logs/search" style={{ marginBottom: 16 }}>
          <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
            <pre>{`{
  "query": "error payment timeout",
  "start_time": "2025-06-16T00:00:00Z",
  "end_time": "2025-06-16T23:59:59Z",
  "log_level": ["ERROR", "WARN"],
  "service_name": ["payment-service"],
  "limit": 100,
  "offset": 0,
  "sort_by": "relevance"
}`}</pre>
          </div>
        </Card>

        <Card size="small" title="GET /api/v1/logs/search" style={{ marginBottom: 16 }}>
          <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
            <Text code>
              GET /api/v1/logs/search?q=error&log_level=ERROR&limit=50
            </Text>
          </div>
        </Card>

        <Title level={3}>Response Format</Title>
        <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
          <pre>{`{
  "query": "error payment",
  "total_hits": 156,
  "execution_time_ms": 45.7,
  "results": [
    {
      "id": "log_123",
      "timestamp": "2025-06-16T10:30:00Z",
      "level": "ERROR",
      "service_name": "payment-service",
      "message": "Payment processing failed",
      "score": 0.95
    }
  ],
  "pagination": {
    "offset": 0,
    "limit": 100,
    "has_more": false
  }
}`}</pre>
        </div>

        <Title level={3}>Rate Limits</Title>
        <Paragraph>
          • Authenticated users: 1000 requests/hour<br/>
          • Anonymous users: 100 requests/hour<br/>
          • Premium users: 10,000 requests/hour
        </Paragraph>

        <Title level={3}>Error Codes</Title>
        <Table
          size="small"
          pagination={false}
          dataSource={[
            { code: 400, description: 'Bad Request - Invalid parameters' },
            { code: 401, description: 'Unauthorized - Invalid or missing token' },
            { code: 429, description: 'Rate Limit Exceeded' },
            { code: 500, description: 'Internal Server Error' }
          ]}
          columns={[
            { title: 'Code', dataIndex: 'code', key: 'code', width: 80 },
            { title: 'Description', dataIndex: 'description', key: 'description' }
          ]}
        />
      </Card>
    </div>
  );
}

export default ApiDocumentation;
