import React, { useState, useEffect } from 'react';
import ErrorTrendChart from '../charts/ErrorTrendChart';
import HeatmapChart from '../charts/HeatmapChart';
import ServiceBarChart from '../charts/ServiceBarChart';
import MetricsCards from './MetricsCards';
import './Dashboard.css';

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ws = null;
    
    const connectWebSocket = () => {
      ws = new WebSocket('ws://localhost:8000/api/v1/visualization/real-time');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'metrics_update') {
            setMetrics(data.data);
            setLoading(false);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('Connection error');
      };
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Real-time Log Analytics</h2>
        <p>Monitor your distributed services with interactive visualizations</p>
      </div>
      
      {metrics && <MetricsCards metrics={metrics} />}
      
      <div className="charts-grid">
        <div className="chart-section">
          <h3>Error Rate Trends (24h)</h3>
          <ErrorTrendChart />
        </div>
        
        <div className="chart-section">
          <h3>Response Time Heatmap</h3>
          <HeatmapChart />
        </div>
        
        <div className="chart-section full-width">
          <h3>Service Performance (Last Hour)</h3>
          <ServiceBarChart />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
