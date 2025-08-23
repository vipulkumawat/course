import React, { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './components/dashboard/Dashboard';
import ChartContainer from './components/charts/ChartContainer';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

function App() {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Check API connection
    fetch('/api/v1/visualization/real-time-metrics')
      .then(response => response.ok && setIsConnected(true))
      .catch(() => setIsConnected(false));
  }, []);

  return (
    <Router>
      <div className="App">
        <header className="app-header">
          <div className="header-content">
            <h1>🔍 Log Visualization Dashboard</h1>
            <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
          <nav className="navigation">
            <Link to="/" className="nav-link">Dashboard</Link>
            <Link to="/charts" className="nav-link">Charts</Link>
          </nav>
        </header>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/charts" element={<ChartContainer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
