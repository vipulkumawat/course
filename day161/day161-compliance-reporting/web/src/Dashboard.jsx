import React, { useState, useEffect } from 'react';

const ComplianceDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard/stats');
      const data = await response.json();
      setStats(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const getStatusColor = (percentage) => {
    if (percentage >= 80) return '#10b981';
    if (percentage >= 60) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return <div className="loading">Loading compliance dashboard...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🛡️ Security Compliance Dashboard</h1>
        <p className="timestamp">Last Updated: {new Date(stats.timestamp).toLocaleString()}</p>
      </header>

      <div className="stats-grid">
        {Object.entries(stats.frameworks).map(([framework, data]) => (
          <div key={framework} className="compliance-card">
            <div className="card-header">
              <h2>{framework.toUpperCase().replace('_', '-')}</h2>
              <span className={`status-badge ${data.status}`}>
                {data.status.toUpperCase()}
              </span>
            </div>
            
            <div className="progress-container">
              <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="10"/>
                <circle 
                  cx="60" 
                  cy="60" 
                  r="50" 
                  fill="none" 
                  stroke={getStatusColor(data.coverage_percentage)}
                  strokeWidth="10"
                  strokeDasharray={`${(data.coverage_percentage / 100) * 314} 314`}
                  transform="rotate(-90 60 60)"
                />
                <text x="60" y="60" textAnchor="middle" dy=".3em" fontSize="24" fontWeight="bold">
                  {data.coverage_percentage.toFixed(0)}%
                </text>
              </svg>
            </div>

            <div className="card-stats">
              <div className="stat">
                <span className="stat-label">Requirements</span>
                <span className="stat-value">
                  {data.requirements_with_evidence} / {data.total_requirements}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Gaps</span>
                <span className="stat-value">{data.gap_count}</span>
              </div>
            </div>

            <button 
              className="report-button"
              onClick={() => generateReport(framework)}
            >
              Generate Report
            </button>
          </div>
        ))}
      </div>

      <div className="evidence-summary">
        <h3>Evidence Summary</h3>
        <p>Total Evidence Collected: <strong>{stats.total_evidence}</strong></p>
      </div>

      <style jsx>{`
        .dashboard {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          max-width: 1400px;
          margin: 0 auto;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }

        .dashboard-header {
          text-align: center;
          color: white;
          margin-bottom: 40px;
        }

        .dashboard-header h1 {
          font-size: 2.5em;
          margin: 0;
        }

        .timestamp {
          color: rgba(255, 255, 255, 0.8);
          margin-top: 10px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 30px;
          margin-bottom: 40px;
        }

        .compliance-card {
          background: white;
          border-radius: 15px;
          padding: 25px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
          transition: transform 0.3s ease;
        }

        .compliance-card:hover {
          transform: translateY(-5px);
        }

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .card-header h2 {
          margin: 0;
          color: #1e40af;
          font-size: 1.3em;
        }

        .status-badge {
          padding: 5px 15px;
          border-radius: 20px;
          font-size: 0.8em;
          font-weight: bold;
        }

        .status-badge.compliant {
          background: #10b981;
          color: white;
        }

        .status-badge.non-compliant {
          background: #ef4444;
          color: white;
        }

        .progress-container {
          display: flex;
          justify-content: center;
          margin: 20px 0;
        }

        .card-stats {
          display: flex;
          justify-content: space-around;
          margin: 20px 0;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-label {
          color: #6b7280;
          font-size: 0.9em;
          margin-bottom: 5px;
        }

        .stat-value {
          font-size: 1.5em;
          font-weight: bold;
          color: #1e40af;
        }

        .report-button {
          width: 100%;
          padding: 12px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1em;
          font-weight: bold;
          cursor: pointer;
          transition: opacity 0.3s ease;
        }

        .report-button:hover {
          opacity: 0.9;
        }

        .evidence-summary {
          background: white;
          padding: 30px;
          border-radius: 15px;
          text-align: center;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .evidence-summary h3 {
          color: #1e40af;
          margin-top: 0;
        }

        .loading {
          text-align: center;
          padding: 50px;
          color: white;
          font-size: 1.5em;
        }
      `}</style>
    </div>
  );
};

const generateReport = async (framework) => {
  try {
    const response = await fetch(`http://localhost:8000/api/reports/generate/${framework}`, {
      method: 'POST'
    });
    const result = await response.json();
    alert(`Report generated: ${result.report_path}\nCoverage: ${result.coverage.toFixed(1)}%\nGaps: ${result.gaps}`);
  } catch (error) {
    alert('Error generating report: ' + error.message);
  }
};

export default ComplianceDashboard;
