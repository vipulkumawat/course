import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async getChaosScenarios() {
    const response = await this.client.get('/api/chaos/scenarios');
    return response.data;
  }

  async createChaosScenario(scenarioData) {
    const response = await this.client.post('/api/chaos/scenarios', scenarioData);
    return response.data;
  }

  async stopChaosScenario(scenarioId) {
    const response = await this.client.post(`/api/chaos/scenarios/${scenarioId}/stop`);
    return response.data;
  }

  async emergencyStop() {
    const response = await this.client.post('/api/chaos/emergency-stop');
    return response.data;
  }

  async getMetrics() {
    const response = await this.client.get('/api/monitoring/metrics');
    return response.data;
  }

  async getMetricsSummary(durationMinutes = 10) {
    const response = await this.client.get(`/api/monitoring/summary?duration_minutes=${durationMinutes}`);
    return response.data;
  }

  async validateRecovery(scenarioId) {
    const response = await this.client.post(`/api/recovery/validate/${scenarioId}`);
    return response.data;
  }

  async getConfig() {
    const response = await this.client.get('/api/config');
    return response.data;
  }

  async getScenarioTemplates() {
    const response = await this.client.get('/api/config/scenarios');
    return response.data;
  }
}

export default new ApiService();
