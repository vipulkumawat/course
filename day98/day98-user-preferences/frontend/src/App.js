import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { PreferenceProvider } from './context/PreferenceContext';
import Dashboard from './components/dashboard/Dashboard';
import PreferencesPage from './components/preferences/PreferencesPage';
import Navigation from './components/common/Navigation';
import './styles/App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <PreferenceProvider>
        <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          <div className="App">
            <Navigation />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/preferences" element={<PreferencesPage />} />
              </Routes>
            </main>
          </div>
        </Router>
      </PreferenceProvider>
    </QueryClientProvider>
  );
}

export default App;
