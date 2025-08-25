import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Common/Layout';
import SavedSearches from './components/SavedSearches/SavedSearches';
import Alerts from './components/Alerts/Alerts';
import NotificationCenter from './components/Alerts/NotificationCenter';
import './styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/searches" replace />} />
            <Route path="/searches" element={<SavedSearches />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/notifications" element={<NotificationCenter />} />
          </Routes>
        </Layout>
        <Toaster position="top-right" />
      </Router>
    </QueryClientProvider>
  );
}

export default App;
