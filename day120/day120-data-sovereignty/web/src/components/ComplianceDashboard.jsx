import React, { useState, useEffect } from 'react';
import './ComplianceDashboard.css';

const ComplianceDashboard = () => {
  const [report, setReport] = useState(null);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [testLog, setTestLog] = useState({
    id: '',
    message: '',
    level: 'INFO',
    service: '',
    ip_address: '',
    user_location: 'EU'
  });
  const [classificationResult, setClassificationResult] = useState(null);
  const [testResults, setTestResults] = useState([]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [reportRes, violationsRes] = await Promise.all([
        fetch('http://localhost:8000/compliance/report'),
        fetch('http://localhost:8000/compliance/violations')
      ]);
      
      setReport(await reportRes.json());
      setViolations(await violationsRes.json());
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const classifyLog = async () => {
    if (!testLog.id || !testLog.message) {
      alert('Please fill in ID and message');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testLog)
      });
      const result = await response.json();
      setClassificationResult(result);
      
      // Add to test results
      setTestResults(prev => [result, ...prev.slice(0, 9)]);
    } catch (error) {
      console.error('Error classifying log:', error);
    }
  };

  const testStorageValidation = async (region) => {
    if (!classificationResult) {
      alert('Please classify a log first');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/validate/storage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          log_entry: testLog,
          target_region: region
        })
      });
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error testing storage:', error);
    }
  };

  const testTransferValidation = async (sourceRegion, targetRegion) => {
    if (!classificationResult) {
      alert('Please classify a log first');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/validate/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          log_entry: testLog,
          source_region: sourceRegion,
          target_region: targetRegion
        })
      });
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error testing transfer:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading compliance data...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🔒 Data Sovereignty Compliance Dashboard</h1>
        <div className="last-updated">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </header>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`tab ${activeTab === 'testing' ? 'active' : ''}`}
          onClick={() => setActiveTab('testing')}
        >
          🧪 Testing
        </button>
        <button 
          className={`tab ${activeTab === 'violations' ? 'active' : ''}`}
          onClick={() => setActiveTab('violations')}
        >
          ⚠️ Violations
        </button>
      </div>

      {activeTab === 'overview' && (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-icon">📊</div>
              <div className="metric-value">{report?.total_events || 0}</div>
              <div className="metric-label">Total Events</div>
            </div>

            <div className="metric-card">
              <div className="metric-icon">⚠️</div>
              <div className="metric-value">{report?.total_violations || 0}</div>
              <div className="metric-label">Violations</div>
            </div>

            <div className="metric-card success">
              <div className="metric-icon">✅</div>
              <div className="metric-value">
                {report?.compliance_rate?.toFixed(1) || 0}%
              </div>
              <div className="metric-label">Compliance Rate</div>
            </div>
          </div>

          <div className="charts-section">
            <div className="chart-card">
              <h2>Storage Distribution by Region</h2>
              <div className="region-bars">
                {report?.storage_by_region && Object.entries(report.storage_by_region).map(([region, count]) => (
                  <div key={region} className="region-bar">
                    <div className="region-name">{region}</div>
                    <div className="bar-container">
                      <div 
                        className="bar-fill"
                        style={{
                          width: `${(count / Math.max(...Object.values(report.storage_by_region))) * 100}%`
                        }}
                      />
                      <span className="bar-value">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="chart-card">
              <h2>Compliance Rate Trend</h2>
              <div className="compliance-gauge">
                <div className="gauge-container">
                  <div className="gauge-circle">
                    <div className="gauge-fill" style={{
                      transform: `rotate(${(report?.compliance_rate || 0) * 1.8 - 90}deg)`
                    }}></div>
                  </div>
                  <div className="gauge-text">
                    <div className="gauge-percentage">{report?.compliance_rate?.toFixed(1) || 0}%</div>
                    <div className="gauge-label">Compliance</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab === 'testing' && (
        <div className="testing-section">
          <div className="test-form">
            <h2>🧪 Test Log Classification</h2>
            <div className="form-grid">
              <div className="form-group">
                <label>Log ID</label>
                <input 
                  type="text" 
                  value={testLog.id}
                  onChange={(e) => setTestLog({...testLog, id: e.target.value})}
                  placeholder="log-001"
                />
              </div>
              <div className="form-group">
                <label>Service</label>
                <input 
                  type="text" 
                  value={testLog.service}
                  onChange={(e) => setTestLog({...testLog, service: e.target.value})}
                  placeholder="auth-service"
                />
              </div>
              <div className="form-group">
                <label>Level</label>
                <select 
                  value={testLog.level}
                  onChange={(e) => setTestLog({...testLog, level: e.target.value})}
                >
                  <option value="INFO">INFO</option>
                  <option value="WARN">WARN</option>
                  <option value="ERROR">ERROR</option>
                </select>
              </div>
              <div className="form-group">
                <label>User Location</label>
                <select 
                  value={testLog.user_location}
                  onChange={(e) => setTestLog({...testLog, user_location: e.target.value})}
                >
                  <option value="EU">EU</option>
                  <option value="US">US</option>
                  <option value="APAC">APAC</option>
                </select>
              </div>
              <div className="form-group full-width">
                <label>Message</label>
                <textarea 
                  value={testLog.message}
                  onChange={(e) => setTestLog({...testLog, message: e.target.value})}
                  placeholder="User john.doe@email.com logged in successfully"
                  rows="3"
                />
              </div>
            </div>
            <button className="classify-btn" onClick={classifyLog}>
              🔍 Classify Log
            </button>
          </div>

          {classificationResult && (
            <div className="classification-result">
              <h3>📋 Classification Result</h3>
              <div className="result-grid">
                <div className="result-item">
                  <span className="result-label">Location:</span>
                  <span className="result-value">{classificationResult.classification?.data_subject_location}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Sensitivity:</span>
                  <span className="result-value">{classificationResult.classification?.sensitivity}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Contains PII:</span>
                  <span className="result-value">{classificationResult.classification?.contains_pii ? 'Yes' : 'No'}</span>
                </div>
                <div className="result-item">
                  <span className="result-label">Regulations:</span>
                  <span className="result-value">{classificationResult.classification?.applicable_regulations?.join(', ')}</span>
                </div>
              </div>

              <div className="validation-tests">
                <h4>🌍 Test Storage Validation</h4>
                <div className="test-buttons">
                  <button onClick={() => testStorageValidation('eu-west-1')}>
                    Test EU Storage
                  </button>
                  <button onClick={() => testStorageValidation('us-east-1')}>
                    Test US Storage
                  </button>
                  <button onClick={() => testStorageValidation('ap-southeast-1')}>
                    Test APAC Storage
                  </button>
                </div>

                <h4>🔄 Test Transfer Validation</h4>
                <div className="test-buttons">
                  <button onClick={() => testTransferValidation('eu-west-1', 'us-east-1')}>
                    EU → US Transfer
                  </button>
                  <button onClick={() => testTransferValidation('us-east-1', 'us-west-2')}>
                    US Internal Transfer
                  </button>
                  <button onClick={() => testTransferValidation('ap-southeast-1', 'eu-west-1')}>
                    APAC → EU Transfer
                  </button>
                </div>
              </div>
            </div>
          )}

          {testResults.length > 0 && (
            <div className="test-history">
              <h3>📜 Test History</h3>
              <div className="history-list">
                {testResults.map((result, idx) => (
                  <div key={idx} className="history-item">
                    <div className="history-header">
                      <span className="history-id">{result.log_id}</span>
                      <span className="history-time">{new Date().toLocaleTimeString()}</span>
                    </div>
                    <div className="history-details">
                      <span className="history-location">{result.classification?.data_subject_location}</span>
                      <span className="history-sensitivity">{result.classification?.sensitivity}</span>
                      <span className="history-pii">{result.classification?.contains_pii ? 'PII' : 'No PII'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'violations' && (
        <div className="violations-section">
          <div className="violations-summary">
            <h2>⚠️ Compliance Violations</h2>
            <div className="violation-stats">
              <div className="stat-item">
                <span className="stat-number">{violations.total_violations || 0}</span>
                <span className="stat-label">Total Violations</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">
                  {report?.violations_by_region ? Object.keys(report.violations_by_region).length : 0}
                </span>
                <span className="stat-label">Affected Regions</span>
              </div>
            </div>
          </div>

          <div className="violations-list-detailed">
            {violations.violations?.map((violation, idx) => (
              <div key={idx} className="violation-item-detailed">
                <div className="violation-header">
                  <span className="violation-id">{violation.log_id}</span>
                  <span className="violation-time">
                    {new Date(violation.timestamp).toLocaleString()}
                  </span>
                  <span className="violation-severity">HIGH</span>
                </div>
                <div className="violation-reason">
                  {violation.decision?.reason || 'Unknown reason'}
                </div>
                <div className="violation-details">
                  <div className="violation-regions">
                    {violation.target_region && (
                      <span className="region-tag">{violation.target_region}</span>
                    )}
                    {violation.source_region && (
                      <span className="region-tag source">{violation.source_region}</span>
                    )}
                  </div>
                  <div className="violation-actions">
                    <button className="action-btn">Investigate</button>
                    <button className="action-btn">Resolve</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplianceDashboard;
