import React, { useState, useEffect } from 'react';
import './App.css';

// Get API URL - use proxy in development
const getApiUrl = () => {
  // In development, React proxy handles this - proxy is configured in package.json
  // The proxy will forward /api/* requests to http://localhost:8000
  if (process.env.NODE_ENV === 'development') {
    return ''; // Use relative URLs, proxy will handle it
  }
  // For production, use the same hostname
  return `http://${window.location.hostname}:8000`;
};

const API_URL = getApiUrl();

function App() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [scanResults, setScanResults] = useState(null);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      // Use proxy in development (empty string), or direct URL in production
      const url = API_URL ? `${API_URL}/stats` : '/stats';
      const response = await fetch(url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setStats(data);
      setApiError(null);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      const apiUrl = API_URL || 'http://localhost:8000 (via proxy)';
      setApiError(`Cannot connect to API at ${apiUrl}. Make sure the API server is running on port 8000.`);
    }
  };

  const scanSampleLogs = async () => {
    const sampleLogs = [
      { ip: "192.168.1.100", action: "login_attempt", user: "admin" },
      { ip: "10.0.0.50", file_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" },
      { domain: "malicious-site.com", action: "dns_query" }
    ];

    try {
      const url = API_URL ? `${API_URL}/scan` : '/scan';
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: sampleLogs })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setScanResults(data);
      setAlerts(data.alerts || []);
      setApiError(null);
    } catch (error) {
      console.error('Scan failed:', error);
      setApiError(`Scan failed: ${error.message}`);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>🔒 IOC Scanner Dashboard</h1>
        <p>Real-time Threat Detection System</p>
      </header>

      <div className="container">
        {apiError && (
          <div className="error-banner">
            <strong>⚠️ Connection Error:</strong> {apiError}
            <br />
            <small>API URL: {API_URL} | Try: http://172.17.32.19:8000 (WSL IP may vary)</small>
          </div>
        )}
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Database Stats</h3>
            {stats?.ioc_database && (
              <div className="stat-content">
                <p><strong>Total IOCs:</strong> {stats.ioc_database.total_iocs.toLocaleString()}</p>
                <p><strong>Lookups:</strong> {stats.ioc_database.lookups.toLocaleString()}</p>
                <p><strong>Cache Hit Rate:</strong> {stats.ioc_database.cache_hit_rate.toFixed(1)}%</p>
              </div>
            )}
          </div>

          <div className="stat-card">
            <h3>Matcher Stats</h3>
            {stats?.matcher && (
              <div className="stat-content">
                <p><strong>Logs Scanned:</strong> {stats.matcher.logs_scanned.toLocaleString()}</p>
                <p><strong>Matches Found:</strong> {stats.matcher.matches_found.toLocaleString()}</p>
                <p><strong>Alerts:</strong> {stats.matcher.alerts_generated.toLocaleString()}</p>
              </div>
            )}
          </div>

          <div className="stat-card">
            <h3>Feed Manager</h3>
            {stats?.feed_manager && (
              <div className="stat-content">
                <p><strong>Feeds Processed:</strong> {stats.feed_manager.feeds_processed}</p>
                <p><strong>IOCs Extracted:</strong> {stats.feed_manager.iocs_extracted.toLocaleString()}</p>
                <p><strong>Last Update:</strong> {stats.feed_manager.last_update ? new Date(stats.feed_manager.last_update).toLocaleString() : 'Never'}</p>
              </div>
            )}
          </div>

          {/* Severity Scoring Depth */}
          <div className="stat-card">
            <h3>📊 Severity Scoring Depth</h3>
            {stats?.severity_scoring && (
              <div className="stat-content">
                <p><strong>Avg Confidence:</strong> {stats.severity_scoring.avg_confidence.toFixed(1)}%</p>
                <div className="severity-breakdown">
                  {Object.entries(stats.severity_scoring.distribution || {}).map(([sev, count]) => (
                    <p key={sev}><strong>{sev.toUpperCase()}:</strong> {count}</p>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* IOC Coverage Breadth */}
          <div className="stat-card">
            <h3>🌐 IOC Coverage Breadth</h3>
            {stats?.ioc_coverage && (
              <div className="stat-content">
                <p><strong>Total Unique IOCs:</strong> {stats.ioc_coverage.total_unique_iocs.toLocaleString()}</p>
                <div className="coverage-breakdown">
                  {Object.entries(stats.ioc_coverage.by_type || {}).map(([type, count]) => (
                    <p key={type}>
                      <strong>{type.replace('_', ' ')}:</strong> {count} 
                      ({stats.ioc_coverage.coverage_percentage[type]?.toFixed(1) || 0}%)
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Performance SLAs */}
          <div className="stat-card">
            <h3>⚡ Performance SLAs</h3>
            {stats?.performance_slas && (
              <div className="stat-content">
                <p><strong>Avg Latency:</strong> {stats.performance_slas.avg_latency_ms.toFixed(2)}ms</p>
                <p><strong>P95 Latency:</strong> {stats.performance_slas.p95_latency_ms.toFixed(2)}ms</p>
                <p><strong>P99 Latency:</strong> {stats.performance_slas.p99_latency_ms.toFixed(2)}ms</p>
                <p><strong>Throughput:</strong> {stats.performance_slas.throughput_logs_per_sec.toFixed(1)} logs/sec</p>
                <p className={stats.performance_slas.sla_compliance_rate >= 95 ? 'sla-met' : 'sla-missed'}>
                  <strong>SLA Compliance:</strong> {stats.performance_slas.sla_compliance_rate.toFixed(1)}%
                  (Target: &lt;{stats.performance_slas.sla_target_ms}ms)
                </p>
              </div>
            )}
          </div>

          {/* Feed Quality Metrics */}
          <div className="stat-card">
            <h3>📈 Feed Quality Metrics</h3>
            {stats?.feed_quality && (
              <div className="stat-content">
                <p><strong>Freshness:</strong> {stats.feed_quality.freshness_hours.toFixed(1)}h 
                  <span className={`status-badge status-${stats.feed_quality.freshness_status}`}>
                    {stats.feed_quality.freshness_status}
                  </span>
                </p>
                <p><strong>Completeness:</strong> {stats.feed_quality.completeness_percentage.toFixed(1)}%</p>
                <p><strong>Accuracy:</strong> {stats.feed_quality.accuracy_percentage.toFixed(1)}%</p>
                <p><strong>Error Rate:</strong> {stats.feed_quality.error_rate.toFixed(2)}%</p>
              </div>
            )}
          </div>

          {/* Alert Lifecycle */}
          <div className="stat-card">
            <h3>🔄 Alert Lifecycle</h3>
            {stats?.alert_lifecycle && (
              <div className="stat-content">
                <p><strong>Total Alerts:</strong> {stats.alert_lifecycle.total_alerts}</p>
                <p><strong>Last 24h:</strong> {stats.alert_lifecycle.recent_alerts_24h}</p>
                <div className="lifecycle-breakdown">
                  {Object.entries(stats.alert_lifecycle.current_state || {}).map(([state, count]) => (
                    <p key={state}>
                      <strong>{state.replace('_', ' ')}:</strong> {count}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="action-section">
          <button onClick={scanSampleLogs} className="scan-button">
            🔍 Scan Sample Logs
          </button>
        </div>

        {scanResults && (
          <div className="results-section">
            <h2>Scan Results</h2>
            <p>Scanned {scanResults.scanned} logs, found {scanResults.alert_count} threats</p>
            
            {alerts.length > 0 && (
              <div className="alerts-list">
                {alerts.map((alert, index) => (
                  <div key={index} className={`alert alert-${alert.severity}`}>
                    <div className="alert-header">
                      <span className="severity-badge">{alert.severity}</span>
                      <span className="confidence">Confidence: {alert.confidence_score.toFixed(1)}%</span>
                    </div>
                    <div className="alert-body">
                      <p><strong>IOC:</strong> {alert.matched_ioc.value}</p>
                      <p><strong>Type:</strong> {alert.matched_ioc.type}</p>
                      <p><strong>Source:</strong> {alert.matched_ioc.source}</p>
                      <p><strong>Description:</strong> {alert.matched_ioc.description}</p>
                      <p><strong>Lifecycle:</strong> <span className="lifecycle-state">{alert.lifecycle_state || 'new'}</span></p>
                      <p><strong>Timestamp:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
