import React, { useState, useEffect } from 'react';
import './Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState({
    total_processors: 0,
    active_processors: 0,
    total_replicas: 0,
    ready_replicas: 0,
    scaling_events: 0
  });
  
  const [processors, setProcessors] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Fetch initial data
    fetchStats();
    fetchProcessors();
    
    // Setup polling
    const interval = setInterval(() => {
      fetchStats();
      fetchProcessors();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      setStats(data);
      setConnected(true);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setConnected(false);
    }
  };

  const fetchProcessors = async () => {
    try {
      const response = await fetch('/api/processors');
      const data = await response.json();
      setProcessors(data);
    } catch (error) {
      console.error('Error fetching processors:', error);
    }
  };

  const getHealthColor = (ready, total) => {
    const ratio = ready / total;
    if (ratio >= 1) return '#10b981';
    if (ratio >= 0.7) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🎛️ Log Platform Operator Dashboard</h1>
        <div className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Processors</div>
          <div className="stat-value">{stats.total_processors}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Active Processors</div>
          <div className="stat-value" style={{ color: '#10b981' }}>
            {stats.active_processors}
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Total Replicas</div>
          <div className="stat-value">{stats.total_replicas}</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Ready Replicas</div>
          <div className="stat-value">
            {stats.ready_replicas} / {stats.total_replicas}
          </div>
        </div>
      </div>

      <div className="processors-section">
        <h2>Log Processors</h2>
        <div className="processors-list">
          {processors.map((proc, idx) => (
            <div key={idx} className="processor-card">
              <div className="processor-header">
                <h3>{proc.name}</h3>
                <span className={`state-badge ${proc.state.toLowerCase()}`}>
                  {proc.state}
                </span>
              </div>
              
              <div className="processor-details">
                <div className="detail-row">
                  <span>Namespace:</span>
                  <span>{proc.namespace}</span>
                </div>
                <div className="detail-row">
                  <span>Log Level:</span>
                  <span className="log-level">{proc.log_level}</span>
                </div>
                <div className="detail-row">
                  <span>Replicas:</span>
                  <span style={{ color: getHealthColor(proc.ready_replicas, proc.replicas) }}>
                    {proc.ready_replicas} / {proc.replicas}
                  </span>
                </div>
                <div className="detail-row">
                  <span>Auto-Scaling:</span>
                  <span>{proc.auto_scaling ? '✅ Enabled' : '❌ Disabled'}</span>
                </div>
              </div>
              
              <div className="replica-status-bar">
                <div 
                  className="replica-fill"
                  style={{ 
                    width: `${(proc.ready_replicas / proc.replicas) * 100}%`,
                    backgroundColor: getHealthColor(proc.ready_replicas, proc.replicas)
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
