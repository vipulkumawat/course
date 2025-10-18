import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import axios from 'axios';
import './App.css';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [replicationMetrics, setReplicationMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [connected, setConnected] = useState(false);
  const [logHistory, setLogHistory] = useState([]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSystemStatus(data);
      setAlerts(data.alerts || []);
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };
    
    return () => ws.close();
  }, []);

  // Fetch replication metrics periodically
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/api/v1/replication/metrics');
        setReplicationMetrics(response.data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const submitTestLog = async () => {
    try {
      const logData = {
        message: `Test log message ${Date.now()}`,
        level: Math.random() > 0.7 ? 'error' : 'info',
        service: ['web-server', 'api-gateway', 'database'][Math.floor(Math.random() * 3)]
      };
      
      const clientInfo = {
        location: ['us', 'eu', 'asia'][Math.floor(Math.random() * 3)],
        client_id: 'test-client'
      };

      const response = await axios.post('/api/v1/logs/submit', logData, {
        params: clientInfo
      });

      setLogHistory(prev => [
        {
          ...logData,
          timestamp: Date.now(),
          result: response.data
        },
        ...prev.slice(0, 9)
      ]);
    } catch (error) {
      console.error('Failed to submit log:', error);
    }
  };

  const triggerFailover = async (regionId) => {
    try {
      await axios.post(`/api/v1/failover/${regionId}`);
    } catch (error) {
      console.error('Failed to trigger failover:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#10B981';
      case 'degraded': return '#F59E0B';
      case 'failed': return '#EF4444';
      case 'recovering': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#3B82F6'];

  // Prepare charts data
  const regionStatusData = systemStatus?.regions?.regions ? 
    Object.entries(systemStatus.regions.regions).map(([id, region]) => ({
      name: id,
      status: region.status,
      latency: region.latency_ms,
      dataCount: region.data_count
    })) : [];

  const replicationLagData = Object.entries(replicationMetrics).map(([region, metrics]) => ({
    region,
    lag: metrics.lag_seconds,
    status: metrics.status
  }));

  return (
    <div className="App">
      <header className="header">
        <h1>🌍 Cross-Region Data Replication</h1>
        <div className="connection-status">
          <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
            {connected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* System Overview */}
        <div className="card">
          <h2>System Overview</h2>
          {systemStatus && (
            <div className="overview-stats">
              <div className="stat">
                <span className="stat-label">Overall Status</span>
                <span className={`stat-value status-${systemStatus.overall_status}`}>
                  {systemStatus.overall_status?.toUpperCase()}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Healthy Regions</span>
                <span className="stat-value">
                  {systemStatus.regions?.healthy_regions || 0}/{systemStatus.regions?.total_regions || 0}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Primary Region</span>
                <span className="stat-value">{systemStatus.regions?.primary_region || 'N/A'}</span>
              </div>
            </div>
          )}
        </div>

        {/* Region Status */}
        <div className="card">
          <h2>Region Health</h2>
          <div className="regions-grid">
            {regionStatusData.map((region) => (
              <div key={region.name} className="region-card">
                <div className="region-header">
                  <span className="region-name">{region.name}</span>
                  <span 
                    className="region-status"
                    style={{ backgroundColor: getStatusColor(region.status) }}
                  >
                    {region.status}
                  </span>
                </div>
                <div className="region-metrics">
                  <div>Latency: {region.latency}ms</div>
                  <div>Data: {region.dataCount}</div>
                  <button 
                    className="failover-btn"
                    onClick={() => triggerFailover(region.name)}
                  >
                    Trigger Failover
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Replication Lag Chart */}
        <div className="card chart-card">
          <h2>Replication Lag</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={replicationLagData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="lag" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Regional Distribution */}
        <div className="card chart-card">
          <h2>Regional Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={regionStatusData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="dataCount"
                nameKey="name"
              >
                {regionStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Test Controls */}
        <div className="card">
          <h2>Test Controls</h2>
          <button className="test-btn" onClick={submitTestLog}>
            Submit Test Log
          </button>
          <div className="log-history">
            <h3>Recent Test Logs</h3>
            {logHistory.map((log, index) => (
              <div key={index} className="log-entry">
                <span className={`log-level ${log.level}`}>{log.level.toUpperCase()}</span>
                <span className="log-service">{log.service}</span>
                <span className="log-message">{log.message}</span>
                <span className="log-region">
                  → {log.result?.routing_result?.target_region}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="card">
          <h2>System Alerts</h2>
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="no-alerts">✅ No active alerts</div>
            ) : (
              alerts.map((alert, index) => (
                <div key={index} className={`alert alert-${alert.severity}`}>
                  <div className="alert-header">
                    <span className="alert-type">{alert.type}</span>
                    <span className="alert-severity">{alert.severity}</span>
                  </div>
                  <div className="alert-message">{alert.message}</div>
                  <div className="alert-time">
                    {new Date(alert.timestamp * 1000).toLocaleTimeString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
