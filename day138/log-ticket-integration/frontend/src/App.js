import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import EventSubmission from './components/EventSubmission';
import TicketManagement from './components/TicketManagement';
import Navigation from './components/Navigation';
import './styles/App.css';

function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <Router>
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/events" element={<EventSubmission />} />
            <Route path="/tickets" element={<TicketManagement />} />
          </Routes>
        </main>
      </Router>
    </div>
  );
}

export default App;
