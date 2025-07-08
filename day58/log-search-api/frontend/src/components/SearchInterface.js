import React, { useState } from 'react';
import { Card, Input, Button, Table, DatePicker, Select, Tag, Space, Row, Col, Statistic, message } from 'antd';
import { SearchOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import moment from 'moment';

const { RangePicker } = DatePicker;
const { Option } = Select;

function SearchInterface() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    logLevel: [],
    serviceName: [],
    dateRange: null
  });

  const logLevels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'];
  const services = ['api-gateway', 'user-service', 'payment-service', 'notification-service'];

  const performSearch = async () => {
    if (!searchQuery.trim()) {
      message.warning('Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      const params = {
        q: searchQuery,
        limit: 50,
        offset: 0
      };

      if (filters.logLevel.length > 0) {
        params.log_level = filters.logLevel;
      }
      
      if (filters.serviceName.length > 0) {
        params.service_name = filters.serviceName;
      }

      if (filters.dateRange) {
        params.start_time = filters.dateRange[0].toISOString();
        params.end_time = filters.dateRange[1].toISOString();
      }

      const response = await axios.get('/api/v1/logs/search', {
        params,
        headers: {
          'Authorization': 'Bearer demo-token'
        }
      });

      setSearchResults(response.data.results || []);
      setStats({
        totalHits: response.data.total_hits,
        executionTime: response.data.execution_time_ms,
        query: response.data.query
      });

      message.success(`Found ${response.data.total_hits} results in ${response.data.execution_time_ms.toFixed(2)}ms`);
    } catch (error) {
      console.error('Search error:', error);
      message.error('Search failed. Please try again.');
      
      // Demo data for UI demonstration
      const demoResults = [
        {
          id: '1',
          timestamp: '2025-06-16T10:30:00Z',
          level: 'ERROR',
          service_name: 'payment-service',
          message: 'Payment processing failed for user 12345',
          score: 0.95
        },
        {
          id: '2', 
          timestamp: '2025-06-16T10:29:45Z',
          level: 'WARN',
          service_name: 'api-gateway',
          message: 'High response time detected: 2.5s',
          score: 0.87
        },
        {
          id: '3',
          timestamp: '2025-06-16T10:29:30Z',
          level: 'INFO',
          service_name: 'user-service',
          message: 'User login successful',
          score: 0.72
        }
      ];
      
      setSearchResults(demoResults);
      setStats({
        totalHits: 156,
        executionTime: 45.7,
        query: searchQuery
      });
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp) => moment(timestamp).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level) => {
        const colors = {
          ERROR: 'red',
          WARN: 'orange', 
          INFO: 'blue',
          DEBUG: 'green',
          FATAL: 'purple'
        };
        return <Tag color={colors[level]}>{level}</Tag>;
      }
    },
    {
      title: 'Service',
      dataIndex: 'service_name',
      key: 'service_name',
      width: 150,
      render: (service) => <Tag color="geekblue">{service}</Tag>
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 80,
      render: (score) => score ? score.toFixed(2) : 'N/A'
    }
  ];

  return (
    <div>
      <Card title="Log Search Interface" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Row gutter={16}>
            <Col span={12}>
              <Input.Search
                placeholder="Enter search query (e.g., error payment timeout)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onSearch={performSearch}
                enterButton={<Button type="primary" icon={<SearchOutlined />}>Search</Button>}
                size="large"
              />
            </Col>
            <Col span={12}>
              <Space>
                <Button icon={<ReloadOutlined />} onClick={() => setSearchResults([])}>
                  Clear
                </Button>
                <Button icon={<DownloadOutlined />} disabled={searchResults.length === 0}>
                  Export
                </Button>
              </Space>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Select
                mode="multiple"
                placeholder="Log Levels"
                style={{ width: '100%' }}
                value={filters.logLevel}
                onChange={(value) => setFilters({...filters, logLevel: value})}
              >
                {logLevels.map(level => (
                  <Option key={level} value={level}>{level}</Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <Select
                mode="multiple"
                placeholder="Services"
                style={{ width: '100%' }}
                value={filters.serviceName}
                onChange={(value) => setFilters({...filters, serviceName: value})}
              >
                {services.map(service => (
                  <Option key={service} value={service}>{service}</Option>
                ))}
              </Select>
            </Col>
            <Col span={8}>
              <RangePicker
                style={{ width: '100%' }}
                showTime
                value={filters.dateRange}
                onChange={(dates) => setFilters({...filters, dateRange: dates})}
              />
            </Col>
            <Col span={4}>
              <Button type="primary" block onClick={performSearch} loading={loading}>
                Apply Filters
              </Button>
            </Col>
          </Row>
        </Space>
      </Card>

      {stats.totalHits && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card>
              <Statistic title="Total Results" value={stats.totalHits} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic 
                title="Execution Time" 
                value={stats.executionTime} 
                suffix="ms"
                precision={2}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="Query" value={`"${stats.query}"`} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="Results Shown" value={searchResults.length} />
            </Card>
          </Col>
        </Row>
      )}

      <Card title="Search Results">
        <Table
          columns={columns}
          dataSource={searchResults}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `Total ${total} items`
          }}
        />
      </Card>
    </div>
  );
}

export default SearchInterface;
