import React, { useState, useEffect } from 'react';
import API_BASE_URL from '../config/api';

const AlertsPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts/recent`);
      const data = await response.json();
      setAlerts(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const getAlertIcon = (type) => {
    const icons = {
      'CPU_CRITICAL': '🔥',
      'MEMORY_CRITICAL': '🧠',
      'RESPONSE_TIME_CRITICAL': '⚡',
      'ERROR_RATE_HIGH': '⚠️'
    };
    return icons[type] || '🚨';
  };

  const getAlertColor = (type) => {
    const colors = {
      'CPU_CRITICAL': 'border-red-200 bg-red-50',
      'MEMORY_CRITICAL': 'border-orange-200 bg-orange-50',
      'RESPONSE_TIME_CRITICAL': 'border-yellow-200 bg-yellow-50',
      'ERROR_RATE_HIGH': 'border-purple-200 bg-purple-50'
    };
    return colors[type] || 'border-red-200 bg-red-50';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">System Alerts</h2>
            <p className="text-sm text-gray-600">Real-time performance alerts and notifications</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Monitoring Active</span>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {alerts.map((alert, index) => (
          <div
            key={`${alert.correlation_id}_${index}`}
            className={`bg-white rounded-xl shadow-md border-2 p-6 ${getAlertColor(alert.type)} hover:shadow-lg transition-shadow duration-300`}
          >
            <div className="flex items-start space-x-4">
              <div className="text-3xl">{getAlertIcon(alert.type)}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {alert.type.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
                  </h3>
                  <span className="text-sm text-gray-500">
                    {alert.timestamp ? new Date(alert.timestamp * 1000).toLocaleString() : 'Just now'}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-white bg-opacity-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 font-medium uppercase tracking-wide">Current Value</p>
                    <p className="text-lg font-bold text-gray-900">
                      {alert.value?.toFixed(1) || 'N/A'}{alert.type.includes('CPU') || alert.type.includes('MEMORY') ? '%' : 'ms'}
                    </p>
                  </div>
                  
                  <div className="bg-white bg-opacity-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 font-medium uppercase tracking-wide">Threshold</p>
                    <p className="text-lg font-bold text-gray-900">
                      {alert.threshold}{alert.type.includes('CPU') || alert.type.includes('MEMORY') ? '%' : 'ms'}
                    </p>
                  </div>
                  
                  <div className="bg-white bg-opacity-50 rounded-lg p-3">
                    <p className="text-xs text-gray-600 font-medium uppercase tracking-wide">Severity</p>
                    <p className="text-lg font-bold text-red-600">Critical</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <code className="text-xs text-gray-500 font-mono bg-white bg-opacity-50 px-2 py-1 rounded">
                    {alert.correlation_id}
                  </code>
                  <div className="flex space-x-2">
                    <button className="px-3 py-1 bg-indigo-600 text-white text-xs rounded-md hover:bg-indigo-700 transition-colors">
                      View Logs
                    </button>
                    <button className="px-3 py-1 bg-gray-600 text-white text-xs rounded-md hover:bg-gray-700 transition-colors">
                      Acknowledge
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {alerts.length === 0 && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center border border-gray-100">
            <div className="text-gray-400 text-4xl mb-4">✅</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Alerts</h3>
            <p className="text-gray-500">All systems are operating within normal parameters.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsPanel;
