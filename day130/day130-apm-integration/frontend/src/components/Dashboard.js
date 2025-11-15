import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, BarChart, Bar } from 'recharts';
import API_BASE_URL from '../config/api';

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentMetrics();
    const interval = setInterval(fetchCurrentMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchCurrentMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/metrics/current`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Ensure we have valid data structure
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      
      setMetrics(data);
      
      // Update historical data
      setHistoricalData(prev => {
        const newData = [...prev, {
          timestamp: new Date((data.timestamp || Date.now() / 1000) * 1000).toLocaleTimeString(),
          cpu: data.system?.cpu || 0,
          memory: data.system?.memory || 0,
          requests: data.application?.request_count || 0,
          responseTime: data.application?.avg_response_time || 0
        }];
        // Keep only last 20 data points
        return newData.slice(-20);
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
      // Set default metrics on error so UI can still render
      setMetrics({
        system: { cpu: 0, memory: 0 },
        application: { request_count: 0, error_count: 0, avg_response_time: 0, p95_response_time: 0, active_connections: 0 },
        timestamp: Date.now() / 1000
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // If no metrics after loading, show error message
  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load metrics</p>
          <p className="text-gray-500 text-sm">Please check if the backend is running on port 8000</p>
        </div>
      </div>
    );
  }

  const MetricCard = ({ title, value, unit, icon, trend }) => (
    <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100 hover:shadow-lg transition-shadow duration-300">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="flex items-center space-x-2">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        <span className="text-sm text-gray-500">{unit}</span>
        {trend && (
          <span className={`text-xs px-2 py-1 rounded-full ${
            trend > 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'
          }`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="CPU Usage"
          value={metrics.system.cpu?.toFixed(1) || '0.0'}
          unit="%"
          icon="💻"
        />
        <MetricCard
          title="Memory Usage"
          value={metrics.system.memory?.toFixed(1) || '0.0'}
          unit="%"
          icon="🧠"
        />
        <MetricCard
          title="Response Time"
          value={metrics.application.avg_response_time?.toFixed(0) || '0'}
          unit="ms"
          icon="⚡"
        />
        <MetricCard
          title="Request Count"
          value={metrics.application.request_count || 0}
          unit="req/min"
          icon="📈"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Metrics Chart */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Performance</h3>
          <LineChart width={400} height={250} data={historicalData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="timestamp" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="cpu" 
              stroke="#3b82f6" 
              strokeWidth={2}
              name="CPU %"
              dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            />
            <Line 
              type="monotone" 
              dataKey="memory" 
              stroke="#10b981" 
              strokeWidth={2}
              name="Memory %"
              dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </div>

        {/* Application Metrics Chart */}
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Application Performance</h3>
          <LineChart width={400} height={250} data={historicalData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="timestamp" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="responseTime" 
              stroke="#f59e0b" 
              strokeWidth={2}
              name="Response Time (ms)"
              dot={{ fill: '#f59e0b', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3 p-4 bg-green-50 rounded-lg">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-green-800">Metrics Collection</p>
              <p className="text-xs text-green-600">Active</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-lg">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-blue-800">Log Correlation</p>
              <p className="text-xs text-blue-600">Running</p>
            </div>
          </div>
          <div className="flex items-center space-x-3 p-4 bg-purple-50 rounded-lg">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <div>
              <p className="text-sm font-medium text-purple-800">Alert Engine</p>
              <p className="text-xs text-purple-600">Monitoring</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
