import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [metrics, setMetrics] = useState(null);
  const [status, setStatus] = useState(null);
  const [failoverHistory, setFailoverHistory] = useState([]);
  const [chaosResults, setChaosResults] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const [metricsRes, statusRes, historyRes, chaosRes] = await Promise.all([
          axios.get(`${apiUrl}/api/metrics`),
          axios.get(`${apiUrl}/api/status`),
          axios.get(`${apiUrl}/api/failover-history`),
          axios.get(`${apiUrl}/api/chaos/results`)
        ]);
        
        setMetrics(metricsRes.data);
        setStatus(statusRes.data);
        setFailoverHistory(historyRes.data.history);
        setChaosResults(chaosRes.data.results);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const triggerFailover = async () => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      await axios.post(`${apiUrl}/api/trigger-failover`);
      alert('Failover triggered successfully');
    } catch (error) {
      alert('Failover failed: ' + error.message);
    }
  };

  const runChaosTest = async (scenario) => {
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      await axios.post(`${apiUrl}/api/chaos/run/${scenario}`);
      alert(`Chaos test "${scenario}" completed`);
    } catch (error) {
      alert('Chaos test failed: ' + error.message);
    }
  };

  if (!metrics || !status) {
    return <div className="loading">Loading DR Dashboard...</div>;
  }

  const drMetrics = metrics.dr_metrics;
  const replMetrics = metrics.replication_metrics;

  return (
    <div className="App">
      <header className="header">
        <h1>🛡️ Disaster Recovery Dashboard</h1>
        <div className="status-badge">
          Status: <span className="status-active">OPERATIONAL</span>
        </div>
      </header>

      <div className="container">
        {/* RTO/RPO Metrics */}
        <div className="card">
          <h2>📊 RTO/RPO Metrics</h2>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">Target RTO</span>
              <span className="metric-value">{metrics.rto_target_seconds}s</span>
            </div>
            <div className="metric">
              <span className="metric-label">Actual Avg RTO</span>
              <span className="metric-value">{drMetrics.average_rto_seconds.toFixed(2)}s</span>
            </div>
            <div className="metric">
              <span className="metric-label">Target RPO</span>
              <span className="metric-value">{metrics.rpo_target_seconds}s</span>
            </div>
            <div className="metric">
              <span className="metric-label">Current RPO</span>
              <span className="metric-value">{drMetrics.last_rpo_seconds.toFixed(2)}s</span>
            </div>
          </div>
        </div>

        {/* Region Status */}
        <div className="card">
          <h2>🌍 Region Status</h2>
          <div className="regions">
            {Object.entries(drMetrics.regions).map(([name, region]) => (
              <div key={name} className="region-card">
                <h3>{name}</h3>
                <div className="region-info">
                  <span className={`badge badge-${region.role}`}>{region.role}</span>
                  <span className={`badge badge-${region.status}`}>{region.status}</span>
                </div>
                <div className="metric-small">
                  Replication Lag: {region.replication_lag_ms}ms
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Replication Metrics */}
        <div className="card">
          <h2>🔄 Replication Metrics</h2>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">Total Replicated</span>
              <span className="metric-value">{replMetrics.total_replicated}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Replication Lag</span>
              <span className="metric-value">{replMetrics.replication_lag_ms.toFixed(0)}ms</span>
            </div>
            <div className="metric">
              <span className="metric-label">Bandwidth</span>
              <span className="metric-value">
                {(replMetrics.bandwidth_bytes_per_sec / 1024 / 1024).toFixed(2)} MB/s
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Compression</span>
              <span className="metric-value">{(replMetrics.compression_ratio * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Failover Statistics */}
        <div className="card">
          <h2>📈 Failover Statistics</h2>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">Total Failovers</span>
              <span className="metric-value">{drMetrics.total_failovers}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Successful</span>
              <span className="metric-value success">{drMetrics.successful_failovers}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Failed</span>
              <span className="metric-value error">{drMetrics.failed_failovers}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Success Rate</span>
              <span className="metric-value">
                {drMetrics.total_failovers > 0 
                  ? ((drMetrics.successful_failovers / drMetrics.total_failovers) * 100).toFixed(1)
                  : 100}%
              </span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="card">
          <h2>⚡ Actions</h2>
          <div className="actions">
            <button onClick={triggerFailover} className="btn btn-danger">
              🔄 Trigger Manual Failover
            </button>
            <button onClick={() => runChaosTest('network_partition')} className="btn btn-warning">
              🌪️ Run Network Partition Test
            </button>
            <button onClick={() => runChaosTest('region_failure')} className="btn btn-warning">
              💥 Run Region Failure Test
            </button>
          </div>
        </div>

        {/* Recent Failovers */}
        {drMetrics.recent_failovers && drMetrics.recent_failovers.length > 0 && (
          <div className="card">
            <h2>📜 Recent Failover Events</h2>
            <div className="timeline">
              {drMetrics.recent_failovers.map((event, idx) => (
                <div key={idx} className="timeline-item">
                  <div className="timeline-time">{new Date(event.timestamp).toLocaleString()}</div>
                  <div className="timeline-content">
                    <strong>{event.from_region} → {event.to_region || 'Failed'}</strong>
                    <div>RTO: {event.rto_seconds?.toFixed(2) || '0.00'}s | RPO: {event.rpo_seconds !== undefined ? event.rpo_seconds.toFixed(2) : 'N/A'}s</div>
                    <span className={`badge badge-${event.status}`}>{event.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chaos Test Results */}
        {chaosResults.length > 0 && (
          <div className="card">
            <h2>🧪 Chaos Engineering Results</h2>
            <div className="test-results">
              {chaosResults.map((result, idx) => (
                <div key={idx} className="test-result">
                  <span className="test-scenario">{result.scenario}</span>
                  <span className={`badge badge-${result.passed ? 'success' : 'error'}`}>
                    {result.passed ? 'PASSED' : 'FAILED'}
                  </span>
                  {result.rto_seconds && (
                    <span className="test-metric">RTO: {result.rto_seconds.toFixed(2)}s</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
