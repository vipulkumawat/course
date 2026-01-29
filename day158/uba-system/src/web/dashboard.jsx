import React, { useState, useEffect } from 'react';

function UBADashboard() {
  const [stats, setStats] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const statsRes = await fetch('/api/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      const alertsRes = await fetch('/api/alerts');
      const alertsData = await alertsRes.json();
      setAlerts(alertsData.alerts || []);
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>🔍 User Behavior Analytics Dashboard</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
        <div style={{ padding: '20px', background: '#e3f2fd', borderRadius: '8px' }}>
          <h3>Total Users</h3>
          <p style={{ fontSize: '2em' }}>{stats.total_users || 0}</p>
        </div>
        <div style={{ padding: '20px', background: '#f3e5f5', borderRadius: '8px' }}>
          <h3>Trained Users</h3>
          <p style={{ fontSize: '2em' }}>{stats.trained_users || 0}</p>
        </div>
        <div style={{ padding: '20px', background: '#ffebee', borderRadius: '8px' }}>
          <h3>High Risk Users</h3>
          <p style={{ fontSize: '2em' }}>{stats.high_risk_users || 0}</p>
        </div>
      </div>

      <h2 style={{ marginTop: '40px' }}>🚨 Recent Alerts</h2>
      <div>
        {alerts.length === 0 ? (
          <p>No alerts</p>
        ) : (
          alerts.map((alert, i) => (
            <div key={i} style={{ 
              padding: '15px', 
              background: alert.risk_level === 'critical' ? '#ffcdd2' : '#fff9c4',
              margin: '10px 0',
              borderRadius: '8px',
              borderLeft: `4px solid ${alert.risk_level === 'critical' ? '#f44336' : '#ff9800'}`
            }}>
              <strong>{alert.user}</strong> - Risk: {alert.risk_score} ({alert.risk_level})
              <br/>
              <small>{new Date(alert.timestamp).toLocaleString()}</small>
              <br/>
              Anomalies: {alert.anomalies.join(', ')}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default UBADashboard;
