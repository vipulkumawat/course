import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('Checking...');
  const [logs, setLogs] = useState([]);
  const [showRedacted, setShowRedacted] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async (endpoint) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/logs/demo/${endpoint}`);
      const data = await response.json();
      setLogs(data);
    } catch (error) {
      setLogs(['Failed to fetch logs']);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(response => response.json())
      .then(data => setApiStatus('Connected'))
      .catch(error => setApiStatus('Disconnected'));

    // Fetch original logs by default
    fetchLogs('original');
  }, []);

  const toggleLogs = () => {
    const newState = !showRedacted;
    setShowRedacted(newState);
    fetchLogs(newState ? 'redacted' : 'original');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Log Redaction System</h1>
        <p>API Status: {apiStatus}</p>
        <p>Frontend running on port 3000</p>
        <p>Backend running on port 8000</p>
        
        <div style={{ margin: '20px 0' }}>
          <button 
            onClick={toggleLogs}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              backgroundColor: showRedacted ? '#ff6b6b' : '#4ecdc4',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            {showRedacted ? 'Show Original Logs' : 'Show Redacted Logs'}
          </button>
        </div>

        <h2>Demo: {showRedacted ? 'Redacted' : 'Original'} Logs</h2>
        {loading ? (
          <p>Loading...</p>
        ) : (
          <ul style={{ 
            textAlign: 'left', 
            maxWidth: 600, 
            margin: '0 auto', 
            background: '#222', 
            padding: 20, 
            borderRadius: 8,
            listStyle: 'none'
          }}>
            {logs.map((log, idx) => (
              <li key={idx} style={{ 
                marginBottom: 10, 
                padding: '8px 0',
                borderBottom: idx < logs.length - 1 ? '1px solid #444' : 'none'
              }}>
                {log}
              </li>
            ))}
          </ul>
        )}
      </header>
    </div>
  );
}

export default App;
