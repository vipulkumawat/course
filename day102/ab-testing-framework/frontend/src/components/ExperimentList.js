import React, { useState } from 'react';
import { Card, Table, Tag, Button, Progress, Space, Modal, Form, Input, Select } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons';

const { Option } = Select;

const ExperimentList = () => {
  const [experiments, setExperiments] = useState([
    {
      id: 1,
      name: 'New Dashboard Layout',
      status: 'running',
      trafficSplit: '50/50',
      significance: 0.03,
      conversionControl: 12.3,
      conversionTreatment: 15.8,
      sampleSize: 2500,
      progress: 75
    },
    {
      id: 2,
      name: 'Enhanced Search Algorithm',
      status: 'paused',
      trafficSplit: '40/60',
      significance: 0.12,
      conversionControl: 8.7,
      conversionTreatment: 9.1,
      sampleSize: 1200,
      progress: 45
    },
    {
      id: 3,
      name: 'Social Login Integration',
      status: 'completed',
      trafficSplit: '50/50',
      significance: 0.01,
      conversionControl: 5.2,
      conversionTreatment: 7.8,
      sampleSize: 5000,
      progress: 100
    }
  ]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const statusColors = {
    running: 'green',
    paused: 'orange',
    completed: 'blue',
    draft: 'default'
  };

  const columns = [
    {
      title: 'Experiment Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <Tag color={statusColors[status]}>{status.toUpperCase()}</Tag>
    },
    {
      title: 'Traffic Split',
      dataIndex: 'trafficSplit',
      key: 'trafficSplit',
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => <Progress percent={progress} />
    },
    {
      title: 'Significance',
      dataIndex: 'significance',
      key: 'significance',
      render: (significance) => (
        <span style={{ color: significance < 0.05 ? '#52c41a' : '#faad14' }}>
          p = {significance.toFixed(3)}
        </span>
      )
    },
    {
      title: 'Control CVR',
      dataIndex: 'conversionControl',
      key: 'conversionControl',
      render: (rate) => `${rate}%`
    },
    {
      title: 'Treatment CVR',
      dataIndex: 'conversionTreatment',
      key: 'conversionTreatment',
      render: (rate) => `${rate}%`
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.status === 'running' && (
            <Button icon={<PauseCircleOutlined />} size="small">Pause</Button>
          )}
          {record.status === 'paused' && (
            <Button icon={<PlayCircleOutlined />} size="small" type="primary">Resume</Button>
          )}
          <Button icon={<StopOutlined />} size="small" danger>Stop</Button>
        </Space>
      )
    }
  ];

  const handleCreateExperiment = (values) => {
    const newExperiment = {
      id: experiments.length + 1,
      name: values.name,
      status: 'draft',
      trafficSplit: `${values.controlPercentage}/${100 - values.controlPercentage}`,
      significance: 1.0,
      conversionControl: 0,
      conversionTreatment: 0,
      sampleSize: 0,
      progress: 0
    };
    
    setExperiments([...experiments, newExperiment]);
    setIsModalVisible(false);
    form.resetFields();
  };

  return (
    <div>
      <Card 
        title="Experiments" 
        extra={
          <Button type="primary" onClick={() => setIsModalVisible(true)}>
            New Experiment
          </Button>
        }
      >
        <Table 
          dataSource={experiments} 
          columns={columns} 
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="Create New Experiment"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          onFinish={handleCreateExperiment}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="Experiment Name"
            rules={[{ required: true, message: 'Please enter experiment name' }]}
          >
            <Input placeholder="Enter experiment name" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="Description"
          >
            <Input.TextArea placeholder="Enter experiment description" />
          </Form.Item>
          
          <Form.Item
            name="controlPercentage"
            label="Control Group Percentage"
            initialValue={50}
            rules={[{ required: true, message: 'Please select control percentage' }]}
          >
            <Select>
              <Option value={10}>10%</Option>
              <Option value={25}>25%</Option>
              <Option value={50}>50%</Option>
              <Option value={75}>75%</Option>
              <Option value={90}>90%</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ExperimentList;
