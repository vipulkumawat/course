import React, { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const submitQuery = async () => {
    setLoading(true);
    try {
      // Use relative path to go through nginx proxy
      const apiUrl = process.env.REACT_APP_API_URL || '/api';
      const response = await fetch(`${apiUrl}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Query failed:', error);
      setResults({ error: error.message });
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ color: '#3b82f6', borderBottom: '3px solid #3b82f6', paddingBottom: '10px' }}>
        📊 Log Processing Dashboard
      </h1>
      
      <div style={{ background: '#f0f7ff', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
        <h2 style={{ marginTop: 0 }}>Natural Language Query</h2>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question (e.g., 'show me errors from the last hour')"
          style={{
            width: '100%',
            padding: '12px',
            fontSize: '16px',
            border: '2px solid #3b82f6',
            borderRadius: '4px',
            marginBottom: '10px'
          }}
          onKeyPress={(e) => e.key === 'Enter' && submitQuery()}
        />
        <button
          onClick={submitQuery}
          disabled={loading}
          style={{
            background: '#3b82f6',
            color: 'white',
            padding: '12px 24px',
            border: 'none',
            borderRadius: '4px',
            fontSize: '16px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          {loading ? 'Processing...' : 'Submit Query'}
        </button>
      </div>

      {results && (
        <div style={{ background: 'white', padding: '20px', borderRadius: '8px', border: '1px solid #e0e0e0' }}>
          <h3 style={{ color: '#3b82f6' }}>Query Results</h3>
          {results.error ? (
            <p style={{ color: 'red' }}>Error: {results.error}</p>
          ) : (
            <div>
              <p><strong>Query:</strong> {results.query}</p>
              <p><strong>Processed by:</strong> {results.processed_by}</p>
              <div style={{ marginTop: '15px' }}>
                <h4>Results:</h4>
                {results.results && results.results.map((log, idx) => (
                  <div key={idx} style={{
                    padding: '10px',
                    margin: '5px 0',
                    background: '#f8f9fa',
                    borderLeft: `4px solid ${log.level === 'ERROR' ? '#dc3545' : '#28a745'}`,
                    borderRadius: '4px'
                  }}>
                    <span style={{ fontWeight: 'bold' }}>[{log.level}]</span> {log.message}
                    <br />
                    <small style={{ color: '#6c757d' }}>{log.timestamp}</small>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div style={{ marginTop: '30px', padding: '15px', background: '#e6f3ff', borderRadius: '8px' }}>
        <h3 style={{ marginTop: 0 }}>🚀 Kubernetes Deployment Status</h3>
        <p>✅ Query Coordinator: Running (3 replicas)</p>
        <p>✅ Storage Nodes: Running (3 replicas)</p>
        <p>✅ RabbitMQ: Running (1 replica)</p>
        <p>✅ Log Collectors: Running (2 replicas)</p>
      </div>
    </div>
  );
}

export default App;
