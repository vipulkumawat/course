import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } from 'recharts';
import { Shield, Users, Database, FileText, Activity, AlertTriangle, CheckCircle, Clock, TrendingUp, Play, Zap, Download, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Dashboard = ({ statistics }) => {
  const [recentRequests, setRecentRequests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshTime, setRefreshTime] = useState(new Date());
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState(0);
  const [showNotification, setShowNotification] = useState(false);
  const [notificationMessage, setNotificationMessage] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    fetchRecentRequests();
    const interval = setInterval(() => {
      setRefreshTime(new Date());
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const showNotificationMessage = (message) => {
    setNotificationMessage(message);
    setShowNotification(true);
    setTimeout(() => setShowNotification(false), 3000);
  };

  const fetchRecentRequests = async () => {
    try {
      // In a real app, you'd fetch recent requests from the API
      // For now, we'll simulate some data
      const mockRequests = [
        { id: '1', user_id: 'user_123', status: 'COMPLETED', created_at: new Date(Date.now() - 3600000) },
        { id: '2', user_id: 'user_456', status: 'PENDING', created_at: new Date(Date.now() - 7200000) },
        { id: '3', user_id: 'user_789', status: 'EXECUTING', created_at: new Date(Date.now() - 10800000) }
      ];
      setRecentRequests(mockRequests);
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching recent requests:', error);
      setIsLoading(false);
    }
  };

  const simulateActions = async () => {
    setIsSimulating(true);
    setSimulationProgress(0);

    try {
      // Step 1: Create sample user data tracking
      setSimulationProgress(20);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const sampleUsers = ['john_doe', 'jane_smith', 'bob_wilson', 'alice_brown', 'charlie_davis'];
      const dataTypes = ['user_profile', 'purchase_history', 'analytics_events', 'support_tickets', 'marketing_preferences'];
      
      for (let i = 0; i < 5; i++) {
        const userData = {
          user_id: sampleUsers[i],
          data_type: dataTypes[i],
          storage_location: `database_${i + 1}`,
          data_path: `/users/${sampleUsers[i]}/data`,
          metadata: { source: 'web_app', version: '1.0' }
        };
        
        await fetch('/api/user-data-tracking', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData)
        });
        
        setSimulationProgress(20 + (i + 1) * 10);
        await new Promise(resolve => setTimeout(resolve, 300));
      }

      // Step 2: Create erasure requests
      setSimulationProgress(70);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      for (let i = 0; i < 3; i++) {
        const erasureRequest = {
          user_id: sampleUsers[i],
          request_type: 'DELETE'
        };
        
        await fetch('/api/erasure-requests', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(erasureRequest)
        });
        
        setSimulationProgress(70 + (i + 1) * 8);
        await new Promise(resolve => setTimeout(resolve, 400));
      }

      // Step 3: Complete simulation
      setSimulationProgress(100);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Refresh data
      window.location.reload();
      
    } catch (error) {
      console.error('Simulation error:', error);
      alert('Simulation completed with some errors. Check console for details.');
    } finally {
      setIsSimulating(false);
      setSimulationProgress(0);
    }
  };

  // Quick Actions Handlers
  const handleNewErasureRequest = () => {
    navigate('/erasure-request');
    showNotificationMessage('Navigating to Erasure Request form...');
  };

  const handleTrackNewData = () => {
    navigate('/data-tracking');
    showNotificationMessage('Navigating to Data Tracking form...');
  };

  const handleGenerateReport = async () => {
    try {
      showNotificationMessage('Generating GDPR compliance report...');
      
      // Simulate report generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create a mock report download
      const reportData = {
        generated_at: new Date().toISOString(),
        total_users: statistics.unique_users,
        total_mappings: statistics.total_mappings,
        total_requests: statistics.total_erasure_requests,
        completion_rate: statistics.completion_rate,
        data_types: statistics.data_types
      };
      
      const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gdpr-report-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      showNotificationMessage('Report generated and downloaded successfully!');
    } catch (error) {
      console.error('Error generating report:', error);
      showNotificationMessage('Error generating report. Please try again.');
    }
  };

  const handleViewAuditLog = async () => {
    try {
      showNotificationMessage('Loading audit log...');
      
      // Simulate loading audit log
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Create a mock audit log
      const auditLog = [
        {
          timestamp: new Date().toISOString(),
          action: 'USER_DATA_TRACKED',
          user_id: 'john_doe',
          details: 'User profile data tracked in database_1'
        },
        {
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          action: 'ERASURE_REQUEST_CREATED',
          user_id: 'jane_smith',
          details: 'Erasure request created for user data deletion'
        },
        {
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          action: 'DATA_ANONYMIZED',
          user_id: 'bob_wilson',
          details: 'User data anonymized successfully'
        }
      ];
      
      // Open audit log in a new window/tab
      const auditWindow = window.open('', '_blank');
      auditWindow.document.write(`
        <html>
          <head>
            <title>GDPR Audit Log</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; }
              .log-entry { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
              .timestamp { color: #666; font-size: 0.9em; }
              .action { font-weight: bold; color: #4285f4; }
              .details { margin-top: 5px; }
            </style>
          </head>
          <body>
            <h1>GDPR Compliance Audit Log</h1>
            ${auditLog.map(entry => `
              <div class="log-entry">
                <div class="timestamp">${new Date(entry.timestamp).toLocaleString()}</div>
                <div class="action">${entry.action}</div>
                <div class="details">User: ${entry.user_id} - ${entry.details}</div>
              </div>
            `).join('')}
          </body>
        </html>
      `);
      auditWindow.document.close();
      
      showNotificationMessage('Audit log opened in new window!');
    } catch (error) {
      console.error('Error loading audit log:', error);
      showNotificationMessage('Error loading audit log. Please try again.');
    }
  };

  if (isLoading || !statistics) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  const dataTypeData = Object.entries(statistics.data_types || {}).map(([type, count]) => ({
    type: type.replace(/_/g, ' ').toUpperCase(),
    count
  }));

  const completionData = [
    { name: 'Completed', value: statistics.completed_erasure_requests, color: '#34a853' },
    { name: 'Pending', value: Math.max(0, statistics.total_erasure_requests - statistics.completed_erasure_requests), color: '#fbbc05' },
    { name: 'Failed', value: Math.max(0, statistics.total_erasure_requests - statistics.completed_erasure_requests - 1), color: '#ea4335' }
  ].filter(item => item.value > 0);

  const trendData = [
    { day: 'Mon', requests: 12, completions: 10 },
    { day: 'Tue', requests: 15, completions: 13 },
    { day: 'Wed', requests: 8, completions: 7 },
    { day: 'Thu', requests: 20, completions: 18 },
    { day: 'Fri', requests: 18, completions: 16 },
    { day: 'Sat', requests: 5, completions: 4 },
    { day: 'Sun', requests: 3, completions: 3 }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="status-icon completed" />;
      case 'PENDING':
        return <Clock className="status-icon pending" />;
      case 'EXECUTING':
        return <Activity className="status-icon executing" />;
      case 'FAILED':
        return <AlertTriangle className="status-icon failed" />;
      default:
        return <Clock className="status-icon pending" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED':
        return '#34a853';
      case 'PENDING':
        return '#fbbc05';
      case 'EXECUTING':
        return '#4285f4';
      case 'FAILED':
        return '#ea4335';
      default:
        return '#9aa0a6';
    }
  };

  return (
    <div className="dashboard">
      {/* Notification */}
      {showNotification && (
        <div className="notification">
          <div className="notification-content">
            <span>{notificationMessage}</span>
            <button onClick={() => setShowNotification(false)} className="notification-close">×</button>
          </div>
        </div>
      )}

      <div className="dashboard-header">
        <div className="dashboard-title">
          <Shield className="dashboard-icon" />
          <h1>GDPR Compliance Dashboard</h1>
        </div>
        <div className="dashboard-refresh">
          <span>Last updated: {refreshTime.toLocaleTimeString()}</span>
          <button onClick={fetchRecentRequests} className="refresh-btn">
            <Activity size={16} />
            Refresh
          </button>
        </div>
      </div>

      {/* Simulation Panel */}
      <div className="simulation-panel">
        <div className="simulation-header">
          <Zap className="simulation-icon" />
          <h3>Demo Actions</h3>
        </div>
        <p>Click the button below to simulate all GDPR compliance actions and populate the dashboard with sample data.</p>
        <button 
          onClick={simulateActions} 
          disabled={isSimulating}
          className={`simulate-btn ${isSimulating ? 'simulating' : ''}`}
        >
          {isSimulating ? (
            <>
              <div className="simulation-spinner"></div>
              Simulating... {simulationProgress}%
            </>
          ) : (
            <>
              <Play size={16} />
              Simulate All Actions
            </>
          )}
        </button>
        {isSimulating && (
          <div className="simulation-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${simulationProgress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>
      
      {/* Key Metrics */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Users />
          </div>
          <div className="stat-content">
            <h3>Total Users Tracked</h3>
            <div className="stat-value">{statistics.unique_users}</div>
            <div className="stat-change positive">+12% from last week</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <Database />
          </div>
          <div className="stat-content">
            <h3>Data Mappings</h3>
            <div className="stat-value">{statistics.total_mappings}</div>
            <div className="stat-change positive">+8% from last week</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <FileText />
          </div>
          <div className="stat-content">
            <h3>Erasure Requests</h3>
            <div className="stat-value">{statistics.total_erasure_requests}</div>
            <div className="stat-change neutral">+2% from last week</div>
          </div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">
            <TrendingUp />
          </div>
          <div className="stat-content">
            <h3>Completion Rate</h3>
            <div className="stat-value">{statistics.completion_rate.toFixed(1)}%</div>
            <div className="stat-change positive">+5% from last week</div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-grid">
        <div className="chart-container">
          <h3>Data Types Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dataTypeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="type" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}
              />
              <Bar dataKey="count" fill="#4285f4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Erasure Request Status</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={completionData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {completionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#fff', 
                  border: '1px solid #e0e0e0',
                  borderRadius: '8px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trend Chart */}
      <div className="chart-container full-width">
        <h3>Weekly Request Trends</h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="day" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#fff', 
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            />
            <Area 
              type="monotone" 
              dataKey="requests" 
              stackId="1" 
              stroke="#4285f4" 
              fill="#4285f4" 
              fillOpacity={0.6} 
            />
            <Area 
              type="monotone" 
              dataKey="completions" 
              stackId="1" 
              stroke="#34a853" 
              fill="#34a853" 
              fillOpacity={0.6} 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Requests */}
      <div className="recent-requests">
        <h3>Recent Erasure Requests</h3>
        <div className="requests-table">
          <div className="table-header">
            <div className="header-cell">Request ID</div>
            <div className="header-cell">User ID</div>
            <div className="header-cell">Status</div>
            <div className="header-cell">Created</div>
            <div className="header-cell">Actions</div>
          </div>
          {recentRequests.map((request) => (
            <div key={request.id} className="table-row">
              <div className="table-cell">{request.id}</div>
              <div className="table-cell">{request.user_id}</div>
              <div className="table-cell">
                <div className="status-badge" style={{ backgroundColor: getStatusColor(request.status) }}>
                  {getStatusIcon(request.status)}
                  {request.status}
                </div>
              </div>
              <div className="table-cell">{request.created_at.toLocaleString()}</div>
              <div className="table-cell">
                <button className="action-btn">View Details</button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="actions-grid">
          <button className="action-card" onClick={handleNewErasureRequest}>
            <FileText size={24} />
            <span>New Erasure Request</span>
          </button>
          <button className="action-card" onClick={handleTrackNewData}>
            <Database size={24} />
            <span>Track New Data</span>
          </button>
          <button className="action-card" onClick={handleGenerateReport}>
            <Download size={24} />
            <span>Generate Report</span>
          </button>
          <button className="action-card" onClick={handleViewAuditLog}>
            <Eye size={24} />
            <span>View Audit Log</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
