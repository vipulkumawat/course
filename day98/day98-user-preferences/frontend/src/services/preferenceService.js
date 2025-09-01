import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Authorization': 'Bearer demo-token', // Mock token for demo
    'Content-Type': 'application/json'
  }
});

export const preferenceService = {
  async getPreferences(category = null) {
    const params = category ? { category } : {};
    const response = await api.get('/preferences', { params });
    return response.data;
  },

  async updatePreference(category, key, value) {
    const response = await api.put('/preferences', {
      category,
      key,
      value
    });
    return response.data;
  },

  async bulkUpdatePreferences(preferences) {
    const response = await api.put('/preferences/bulk', {
      preferences
    });
    return response.data;
  },

  async getDefaultPreferences(category = null) {
    const params = category ? { category } : {};
    const response = await api.get('/preferences/defaults', { params });
    return response.data;
  }
};
