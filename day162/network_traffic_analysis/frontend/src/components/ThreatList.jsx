import React from 'react';
import './ThreatList.css';

function ThreatList({ threats }) {
  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'critical': return 'severity-critical';
      case 'high': return 'severity-high';
      case 'medium': return 'severity-medium';
      default: return 'severity-low';
    }
  };
  
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'medium': return '🟡';
      default: return '🟢';
    }
  };
  
  return (
    <div className="threat-list">
      <h2>🚨 Active Threats</h2>
      
      {threats.length === 0 ? (
        <div className="no-threats">
          <p>✅ No active threats detected</p>
        </div>
      ) : (
        <div className="threats-container">
          {threats.map((threat, index) => (
            <div key={index} className={`threat-card ${getSeverityClass(threat.severity)}`}>
              <div className="threat-header">
                <span className="threat-icon">{getSeverityIcon(threat.severity)}</span>
                <span className="threat-type">{threat.type.replace('_', ' ').toUpperCase()}</span>
                <span className="threat-score">{threat.threat_score}/100</span>
              </div>
              <div className="threat-details">
                <p><strong>Source:</strong> {threat.source_ip}</p>
                <p><strong>Details:</strong> {threat.details}</p>
                <p className="threat-time">
                  {new Date(threat.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ThreatList;
