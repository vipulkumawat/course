import React from 'react';
import './MetricsPanel.css';

function MetricsPanel({ metrics }) {
  if (!metrics) {
    return <div className="metrics-panel">Loading...</div>;
  }
  
  const formatBytes = (bytes) => {
    if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(2) + ' GB';
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(2) + ' MB';
    if (bytes >= 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return bytes + ' B';
  };
  
  return (
    <div className="metrics-panel">
      <div className="metric-card">
        <div className="metric-icon">🔗</div>
        <div className="metric-content">
          <div className="metric-value">{metrics.total_connections || 0}</div>
          <div className="metric-label">Total Connections</div>
        </div>
      </div>
      
      <div className="metric-card">
        <div className="metric-icon">📊</div>
        <div className="metric-content">
          <div className="metric-value">{(metrics.connections_per_second || 0).toFixed(1)}/s</div>
          <div className="metric-label">Connections Rate</div>
        </div>
      </div>
      
      <div className="metric-card">
        <div className="metric-icon">💾</div>
        <div className="metric-content">
          <div className="metric-value">{formatBytes(metrics.total_bytes || 0)}</div>
          <div className="metric-label">Total Traffic</div>
        </div>
      </div>
      
      <div className="metric-card">
        <div className="metric-icon">🌐</div>
        <div className="metric-content">
          <div className="metric-value">{metrics.unique_sources || 0}</div>
          <div className="metric-label">Unique Sources</div>
        </div>
      </div>
    </div>
  );
}

export default MetricsPanel;
