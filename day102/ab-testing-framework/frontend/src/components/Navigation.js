import React from 'react';
import { Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { DashboardOutlined, ExperimentOutlined, FlagOutlined } from '@ant-design/icons';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard'
    },
    {
      key: '/experiments',
      icon: <ExperimentOutlined />,
      label: 'Experiments'
    },
    {
      key: '/feature-flags',
      icon: <FlagOutlined />,
      label: 'Feature Flags'
    }
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Menu
      mode="inline"
      selectedKeys={[location.pathname]}
      items={menuItems}
      onClick={handleMenuClick}
    />
  );
};

export default Navigation;
