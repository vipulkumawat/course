import React from 'react';
import { usePreferences } from '../../context/PreferenceContext';
import { Monitor, Users, Activity } from 'lucide-react';

const Dashboard = () => {
  const { preferences } = usePreferences();
  
  const theme = preferences.theme?.theme || 'light';
  const autoRefresh = preferences.dashboard?.auto_refresh || false;
  const refreshInterval = preferences.dashboard?.refresh_interval || 30;

  return (
    <div className={`dashboard ${theme}`}>
      <div className="dashboard-header">
        <h1>Log Processing Dashboard</h1>
        <div className="dashboard-stats">
          <div className="stat-item">
            <Monitor className="stat-icon" />
            <div className="stat-content">
              <span className="stat-value">12</span>
              <span className="stat-label">Active Systems</span>
            </div>
          </div>
          <div className="stat-item">
            <Users className="stat-icon" />
            <div className="stat-content">
              <span className="stat-value">247</span>
              <span className="stat-label">Online Users</span>
            </div>
          </div>
          <div className="stat-item">
            <Activity className="stat-icon" />
            <div className="stat-content">
              <span className="stat-value">98.7%</span>
              <span className="stat-label">System Health</span>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-widgets">
        <div className="widget">
          <h3>System Performance</h3>
          <div className="widget-content">
            <p>Auto-refresh: {autoRefresh ? 'Enabled' : 'Disabled'}</p>
            <p>Refresh interval: {refreshInterval} seconds</p>
            <p>Theme: {theme}</p>
          </div>
        </div>
        
        <div className="widget">
          <h3>Recent Logs</h3>
          <div className="widget-content">
            <div className="log-item">
              <span className="log-level info">INFO</span>
              <span className="log-message">User login successful</span>
              <span className="log-time">2 minutes ago</span>
            </div>
            <div className="log-item">
              <span className="log-level warning">WARN</span>
              <span className="log-message">High CPU usage detected</span>
              <span className="log-time">5 minutes ago</span>
            </div>
            <div className="log-item">
              <span className="log-level error">ERROR</span>
              <span className="log-message">Database connection failed</span>
              <span className="log-time">8 minutes ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
