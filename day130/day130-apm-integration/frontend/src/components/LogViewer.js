import React, { useState, useEffect } from 'react';
import API_BASE_URL from '../config/api';

const LogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/logs/recent?hours=1`);
      const data = await response.json();
      setLogs(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true;
    if (filter === 'critical') return log.enhancement_level === 'CRITICAL';
    if (filter === 'high') return log.enhancement_level === 'HIGH';
    return log.enhancement_level === 'NORMAL';
  });

  const getEnhancementBadge = (level) => {
    const badges = {
      'CRITICAL': 'bg-red-100 text-red-800 border-red-200',
      'HIGH': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'NORMAL': 'bg-green-100 text-green-800 border-green-200'
    };
    return badges[level] || badges['NORMAL'];
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
      {/* Controls */}
      <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Enriched Logs</h2>
          <div className="flex items-center space-x-4">
            <label className="text-sm text-gray-600">Filter by enhancement:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="normal">Normal</option>
            </select>
            <button
              onClick={fetchLogs}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm hover:bg-indigo-700 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Log Entries */}
      <div className="space-y-4">
        {filteredLogs.map((log, index) => (
          <div
            key={log.correlation_id || index}
            className="bg-white rounded-xl shadow-md border border-gray-100 hover:shadow-lg transition-shadow duration-300"
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 text-xs font-medium rounded-md border ${getEnhancementBadge(log.enhancement_level)}`}>
                    {log.enhancement_level}
                  </span>
                  <span className="text-sm text-gray-500">
                    {new Date(log.timestamp * 1000).toLocaleString()}
                  </span>
                </div>
                <code className="text-xs text-gray-400 font-mono">{log.correlation_id}</code>
              </div>

              {/* Original Log */}
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Original Log Entry</h4>
                <div className="bg-gray-50 rounded-lg p-3">
                  <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
                    {JSON.stringify(log.original_log, null, 2)}
                  </pre>
                </div>
              </div>

              {/* Metrics Context */}
              {log.metrics_context && Object.keys(log.metrics_context).length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Context</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(log.metrics_context).map(([key, value]) => (
                      <div key={key} className="bg-indigo-50 rounded-lg p-3">
                        <p className="text-xs text-indigo-600 font-medium uppercase tracking-wide">
                          {key.replace('_', ' ')}
                        </p>
                        <p className="text-sm font-semibold text-indigo-900">
                          {typeof value === 'number' ? value.toFixed(2) : value}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {filteredLogs.length === 0 && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center border border-gray-100">
            <div className="text-gray-400 text-4xl mb-4">📄</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No logs found</h3>
            <p className="text-gray-500">No logs match the current filter criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogViewer;
