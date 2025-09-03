import React, { useState } from 'react';
import { Card, Table, Switch, Button, Modal, Form, Input, Slider, Space, Tag } from 'antd';
import { SettingOutlined, EditOutlined } from '@ant-design/icons';

const FeatureFlagManager = () => {
  const [flags, setFlags] = useState([
    {
      id: 1,
      name: 'new-dashboard',
      description: 'New dashboard layout with improved UX',
      enabled: true,
      rolloutPercentage: 85,
      environment: 'production'
    },
    {
      id: 2,
      name: 'enhanced-search',
      description: 'Machine learning powered search algorithm',
      enabled: true,
      rolloutPercentage: 62,
      environment: 'production'
    },
    {
      id: 3,
      name: 'social-login',
      description: 'Social media login integration',
      enabled: false,
      rolloutPercentage: 0,
      environment: 'staging'
    },
    {
      id: 4,
      name: 'dark-mode',
      description: 'Dark mode theme support',
      enabled: true,
      rolloutPercentage: 91,
      environment: 'production'
    }
  ]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingFlag, setEditingFlag] = useState(null);
  const [form] = Form.useForm();

  const toggleFlag = (id, enabled) => {
    setFlags(flags.map(flag => 
      flag.id === id ? { ...flag, enabled } : flag
    ));
  };

  const updateRollout = (id, rolloutPercentage) => {
    setFlags(flags.map(flag => 
      flag.id === id ? { ...flag, rolloutPercentage } : flag
    ));
  };

  const environmentColors = {
    production: 'green',
    staging: 'orange',
    development: 'blue'
  };

  const columns = [
    {
      title: 'Flag Name',
      dataIndex: 'name',
      key: 'name',
      render: (name) => <code>{name}</code>
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Environment',
      dataIndex: 'environment',
      key: 'environment',
      render: (env) => <Tag color={environmentColors[env]}>{env}</Tag>
    },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled, record) => (
        <Switch 
          checked={enabled} 
          onChange={(checked) => toggleFlag(record.id, checked)}
        />
      )
    },
    {
      title: 'Rollout %',
      dataIndex: 'rolloutPercentage',
      key: 'rolloutPercentage',
      render: (percentage, record) => (
        <div style={{ width: 100 }}>
          <Slider
            value={percentage}
            onChange={(value) => updateRollout(record.id, value)}
            disabled={!record.enabled}
            tooltip={{ formatter: (value) => `${value}%` }}
          />
        </div>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            icon={<EditOutlined />} 
            size="small"
            onClick={() => {
              setEditingFlag(record);
              form.setFieldsValue(record);
              setIsModalVisible(true);
            }}
          >
            Edit
          </Button>
          <Button icon={<SettingOutlined />} size="small">Configure</Button>
        </Space>
      )
    }
  ];

  const handleSaveFlag = (values) => {
    if (editingFlag) {
      setFlags(flags.map(flag => 
        flag.id === editingFlag.id ? { ...flag, ...values } : flag
      ));
    } else {
      const newFlag = {
        id: flags.length + 1,
        ...values,
        enabled: false,
        rolloutPercentage: 0
      };
      setFlags([...flags, newFlag]);
    }
    
    setIsModalVisible(false);
    setEditingFlag(null);
    form.resetFields();
  };

  return (
    <div>
      <Card 
        title="Feature Flags" 
        extra={
          <Button 
            type="primary" 
            onClick={() => {
              setEditingFlag(null);
              setIsModalVisible(true);
            }}
          >
            New Feature Flag
          </Button>
        }
      >
        <Table 
          dataSource={flags} 
          columns={columns} 
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingFlag ? "Edit Feature Flag" : "Create Feature Flag"}
        visible={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingFlag(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          onFinish={handleSaveFlag}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="Flag Name"
            rules={[{ required: true, message: 'Please enter flag name' }]}
          >
            <Input placeholder="feature-flag-name" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <Input.TextArea placeholder="Describe what this flag controls" />
          </Form.Item>
          
          <Form.Item
            name="environment"
            label="Environment"
            initialValue="staging"
          >
            <Input placeholder="staging, production, development" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default FeatureFlagManager;
