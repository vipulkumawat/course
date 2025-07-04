import React from 'react';

const StatsBar = ({ totalLogs, queryTime, filterCount }) => {
  return (
    <div className="stats-bar">
      <div className="stat-item">
        <div className="stat-value">{totalLogs?.toLocaleString() || '0'}</div>
        <div className="stat-label">Total Logs</div>
      </div>
      <div className="stat-item">
        <div className="stat-value">{queryTime?.toFixed(1) || '0'}ms</div>
        <div className="stat-label">Query Time</div>
      </div>
      <div className="stat-item">
        <div className="stat-value">{filterCount || 0}</div>
        <div className="stat-label">Active Filters</div>
      </div>
    </div>
  );
};

export default StatsBar;
