import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './Dashboard.css';

function Dashboard({ metrics }) {
  const [chartData, setChartData] = useState([]);
  const [protocolData, setProtocolData] = useState([]);
  
  useEffect(() => {
    if (metrics) {
      // Update time series data
      setChartData(prev => {
        const newData = [...prev, {
          time: new Date(metrics.timestamp).toLocaleTimeString(),
          connections: metrics.total_connections,
          bytes: Math.round(metrics.total_bytes / 1024)
        }];
        return newData.slice(-20); // Keep last 20 points
      });
      
      // Update protocol distribution
      if (metrics.protocols) {
        const data = Object.entries(metrics.protocols).map(([name, value]) => ({
          name,
          value
        }));
        setProtocolData(data);
      }
    }
  }, [metrics]);
  
  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'];
  
  if (!metrics) {
    return (
      <div className="dashboard">
        <h2>Traffic Analytics</h2>
        <p>Loading metrics...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h2>Traffic Analytics</h2>
      
      <div className="chart-grid">
        <div className="chart-container">
          <h3>Connection Rate Over Time</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="connections" stroke="#667eea" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <p>Collecting data... Chart will appear shortly.</p>
            </div>
          )}
        </div>
        
        <div className="chart-container">
          <h3>Protocol Distribution</h3>
          {protocolData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={protocolData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {protocolData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ padding: '20px', textAlign: 'center' }}>
              <p>No protocol data available yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
