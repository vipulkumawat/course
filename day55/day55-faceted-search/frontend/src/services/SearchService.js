class SearchService {
  constructor() {
    this.baseURL = 'http://localhost:8000/api';
  }

  async search(searchRequest) {
    try {
      const response = await fetch(`${this.baseURL}/search/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchRequest),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Search response:', data);
      return data;
    } catch (error) {
      console.error('Search service error:', error);
      throw error;
    }
  }

  async getFacets(filters = {}) {
    try {
      const response = await fetch(`${this.baseURL}/search/facets`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Facets service error:', error);
      throw error;
    }
  }

  async generateLogs(count = 100) {
    try {
      const response = await fetch(`${this.baseURL}/logs/generate?count=${count}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Log generation service error:', error);
      throw error;
    }
  }

  async getStats() {
    try {
      const response = await fetch(`${this.baseURL}/search/stats`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Stats service error:', error);
      throw error;
    }
  }
}

export default SearchService;
