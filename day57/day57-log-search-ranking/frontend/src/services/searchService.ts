import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface SearchQuery {
  query: string;
  context?: {
    mode: string;
    user_focus: string;
  };
  limit?: number;
}

export interface SearchResponse {
  query: string;
  results: any[];
  total_hits: number;
  ranked_hits: number;
  execution_time_ms: number;
}

export const searchLogs = async (query: SearchQuery): Promise<SearchResponse> => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/search`, query);
    return response.data;
  } catch (error) {
    console.error('Search API error:', error);
    throw new Error('Failed to search logs');
  }
};

export const getSearchSuggestions = async (query: string): Promise<string[]> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/search/suggestions?q=${encodeURIComponent(query)}`);
    return response.data.suggestions || [];
  } catch (error) {
    console.error('Suggestions API error:', error);
    return [];
  }
};

export const getSearchStats = async (): Promise<any> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/search/stats`);
    return response.data;
  } catch (error) {
    console.error('Stats API error:', error);
    return {
      search_stats: { total_documents: 0, total_searches: 0, avg_response_time_ms: 0 },
      ranking_stats: { total_rankings: 0, context_adjustments: 0 }
    };
  }
}; 