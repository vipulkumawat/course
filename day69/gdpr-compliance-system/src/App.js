import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ErasureRequestForm from './components/ErasureRequestForm';
import DataTrackingForm from './components/DataTrackingForm';
import Dashboard from './components/Dashboard';
import RequestStatus from './components/RequestStatus';
import './styles/App.css';

function App() {
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/statistics');
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/" className="nav-logo">
              GDPR Compliance System
            </Link>
            <div className="nav-menu">
              <Link to="/" className="nav-link">Dashboard</Link>
              <Link to="/erasure-request" className="nav-link">Request Erasure</Link>
              <Link to="/data-tracking" className="nav-link">Track Data</Link>
            </div>
          </div>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard statistics={statistics} />} />
            <Route path="/erasure-request" element={<ErasureRequestForm />} />
            <Route path="/data-tracking" element={<DataTrackingForm />} />
            <Route path="/request-status/:requestId" element={<RequestStatus />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
