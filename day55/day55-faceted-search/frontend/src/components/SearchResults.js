import React from 'react';

const SearchResults = ({ results, selectedFilters }) => {
  if (!results || !results.logs) {
    return <div className="loading">No results found</div>;
  }

  const { logs, total_count } = results;

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatResponseTime = (responseTime) => {
    if (!responseTime) return 'N/A';
    return `${responseTime}ms`;
  };

  return (
    <div className="search-results-container">
      <div className="results-header">
        <div className="results-stats">
          Showing {logs.length} of {total_count} results
        </div>
      </div>

      <div className="results-list">
        {logs.map((log) => (
          <div key={log.id} className="log-entry">
            <div className="log-header">
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className={`log-level ${log.level}`}>{log.level}</span>
                <span className="log-service">{log.service}</span>
              </div>
              <span className="log-timestamp">{formatTimestamp(log.timestamp)}</span>
            </div>
            
            <div className="log-message">{log.message}</div>
            
            <div className="log-metadata">
              {log.region && (
                <span className="metadata-item">📍 {log.region}</span>
              )}
              {log.response_time && (
                <span className="metadata-item">⏱️ {formatResponseTime(log.response_time)}</span>
              )}
              {log.request_id && (
                <span className="metadata-item">🔗 {log.request_id}</span>
              )}
              {log.source_ip && (
                <span className="metadata-item">🌐 {log.source_ip}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {logs.length === 0 && (
        <div className="no-results">
          <p>No logs match your current filters.</p>
          <p>Try adjusting your search criteria or filters.</p>
        </div>
      )}
    </div>
  );
};

export default SearchResults;
