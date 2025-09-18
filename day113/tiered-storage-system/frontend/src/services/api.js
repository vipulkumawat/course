import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Statistics
export const getStatistics = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};

// Log operations
export const storeLogEntry = async (logData) => {
  const response = await api.post('/api/logs', logData);
  return response.data;
};

export const getLogEntry = async (entryId) => {
  const response = await api.get(`/api/logs/${entryId}`);
  return response.data;
};

export const searchLogs = async (query, tier = null) => {
  const params = { q: query };
  if (tier) params.tier = tier;
  
  const response = await api.get('/api/search', { params });
  return response.data;
};

// Migration
export const triggerAutoMigration = async () => {
  const response = await api.post('/api/auto-migrate');
  return response.data;
};

export const manualMigration = async (migrationData) => {
  const response = await api.post('/api/migrate', migrationData);
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export default api;
