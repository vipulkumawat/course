import React, { useState } from 'react';

const LoadSimulator = ({ onLoadComplete }) => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState({});

  const simulateLoad = async (tenantId) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/simulate-load/${tenantId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Tenant-ID': tenantId
        }
      });
      
      const result = await response.json();
      setResults(prev => ({ ...prev, [tenantId]: result }));
      
      if (onLoadComplete) {
        onLoadComplete();
      }
    } catch (error) {
      console.error(`Error simulating load for ${tenantId}:`, error);
      setResults(prev => ({ 
        ...prev, 
        [tenantId]: { error: 'Failed to simulate load' }
      }));
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResults({});
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '25px',
      marginBottom: '30px',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    }}>
      <h3>🧪 Load Simulation Testing</h3>
      <p>Test quota enforcement by simulating load on different tenants</p>
      
      <div className="actions">
        <button 
          className="btn btn-primary"
          onClick={() => simulateLoad('tenant-basic')}
          disabled={loading}
        >
          Test Basic Tenant
        </button>
        <button 
          className="btn btn-primary"
          onClick={() => simulateLoad('tenant-premium')}
          disabled={loading}
        >
          Test Premium Tenant
        </button>
        <button 
          className="btn btn-primary"
          onClick={() => simulateLoad('tenant-enterprise')}
          disabled={loading}
        >
          Test Enterprise Tenant
        </button>
        <button 
          className="btn"
          onClick={clearResults}
          style={{ background: '#6c757d', color: 'white' }}
        >
          Clear Results
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', color: '#666', margin: '20px 0' }}>
          <div className="loading">🔄 Simulating load...</div>
        </div>
      )}

      {Object.entries(results).length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4>Test Results:</h4>
          {Object.entries(results).map(([tenantId, result]) => (
            <div key={tenantId} style={{
              background: '#f8f9fa',
              padding: '15px',
              borderRadius: '8px',
              margin: '10px 0',
              borderLeft: '4px solid #667eea'
            }}>
              <strong>{tenantId}:</strong>
              {result.error ? (
                <span style={{ color: '#dc3545' }}> {result.error}</span>
              ) : (
                <div>
                  <div>Total Requests: {result.total_requests}</div>
                  <div style={{ color: '#28a745' }}>Successful: {result.successful_requests}</div>
                  <div style={{ color: '#dc3545' }}>Failed: {result.failed_requests}</div>
                  <div style={{ marginTop: '5px', fontSize: '14px', color: '#666' }}>
                    {result.message}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LoadSimulator;
