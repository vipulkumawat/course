import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import ThreatList from './components/ThreatList';
import TrafficGraph from './components/TrafficGraph';
import MetricsPanel from './components/MetricsPanel';
import './App.css';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [threats, setThreats] = useState([]);
  const [topology, setTopology] = useState({ nodes: [], edges: [] });
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Fetch initial data via REST API
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/metrics');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Fetched metrics:', data);
        // Convert API response to metrics format expected by components
        const metricsData = {
          timestamp: data.timestamp || new Date().toISOString(),
          total_connections: data.total_connections || data.connections || 0,
          unique_sources: data.unique_sources || data.unique_ips || 0,
          unique_destinations: data.unique_destinations || 0,
          total_bytes: data.total_bytes || data.bytes_transferred || 0,
          connections_per_second: data.connections_per_second || 0,
          bytes_per_second: data.bytes_per_second || 0,
          protocols: data.protocols || {}
        };
        setMetrics(metricsData);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    const fetchThreats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/threats');
        const data = await response.json();
        setThreats(data || []);
      } catch (error) {
        console.error('Failed to fetch threats:', error);
      }
    };

    // Initial fetch
    fetchMetrics();
    fetchThreats();
    fetchTopology();

    // Poll for updates every 2 seconds
    const metricsInterval = setInterval(fetchMetrics, 2000);
    const threatsInterval = setInterval(fetchThreats, 5000);
    const topologyInterval = setInterval(fetchTopology, 3000);

    // Try WebSocket connection
    let ws = null;
    try {
      ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.metrics) {
            setMetrics(data.metrics);
          }
          if (data.threats) {
            setThreats(data.threats);
          }
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setWsConnected(false);
    }
    
    return () => {
      if (ws) ws.close();
      clearInterval(metricsInterval);
      clearInterval(threatsInterval);
      clearInterval(topologyInterval);
    };
  }, []);
  
  const fetchTopology = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/topology');
      const data = await response.json();
      setTopology(data);
    } catch (error) {
      console.error('Failed to fetch topology:', error);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛡️ Network Traffic Analysis System</h1>
        <div className="status">
          <span className={wsConnected ? 'status-connected' : 'status-disconnected'}>
            {wsConnected ? '● Live' : '○ Disconnected'}
          </span>
        </div>
      </header>
      
      <div className="app-content">
        <MetricsPanel metrics={metrics} />
        
        <div className="main-grid">
          <div className="chart-section">
            <Dashboard metrics={metrics} />
          </div>
          
          <div className="threat-section">
            <ThreatList threats={threats} />
          </div>
        </div>
        
        <div className="topology-section">
          <TrafficGraph topology={topology} threats={threats} />
        </div>
      </div>
    </div>
  );
}

export default App;
