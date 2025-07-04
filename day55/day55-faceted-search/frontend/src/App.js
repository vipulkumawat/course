import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import SearchService from './services/SearchService';
import FacetPanel from './components/FacetPanel';
import SearchResults from './components/SearchResults';
import SearchBox from './components/SearchBox';
import StatsBar from './components/StatsBar';

// Create SearchService instance outside component to prevent recreation
const searchService = new SearchService();

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState({});
  const [searchResults, setSearchResults] = useState(null);
  const [facets, setFacets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ total_logs: 0, query_time_ms: 0 });

  const performSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const searchRequest = {
        query: searchQuery,
        filters: selectedFilters,
        limit: 50,
        offset: 0
      };
      
      console.log('Performing search:', searchRequest);
      const result = await searchService.search(searchRequest);
      
      setSearchResults(result);
      setFacets(result.facets || []);
      setStats({
        total_logs: result.total_count,
        query_time_ms: result.query_time_ms
      });
    } catch (err) {
      console.error('Search error:', err);
      setError(`Search failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedFilters]);

  // Initial search on component mount
  useEffect(() => {
    performSearch();
  }, [performSearch]);

  // Debounced search effect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      performSearch();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, selectedFilters]);

  const handleSearchChange = (query) => {
    setSearchQuery(query);
  };

  const handleFilterChange = (facetName, values) => {
    const newFilters = { ...selectedFilters };
    if (values.length > 0) {
      newFilters[facetName] = values;
    } else {
      delete newFilters[facetName];
    }
    setSelectedFilters(newFilters);
  };

  const generateSampleData = async () => {
    setLoading(true);
    try {
      await searchService.generateLogs(500);
      // Refresh search after generation
      await performSearch();
    } catch (err) {
      setError(`Failed to generate sample data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="header">
        <h1>🔍 Faceted Log Search</h1>
        <p>Multi-dimensional filtering for distributed log analysis</p>
        <button 
          onClick={generateSampleData} 
          style={{
            marginTop: '10px',
            padding: '8px 16px',
            backgroundColor: '#1a73e8',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Generate Sample Data (500 logs)
        </button>
      </div>

      <div className="main-content">
        <div className="facets-panel">
          <h3 style={{ margin: '0 0 16px 0', color: '#3c4043' }}>Filters</h3>
          <FacetPanel 
            facets={facets}
            selectedFilters={selectedFilters}
            onFilterChange={handleFilterChange}
          />
        </div>

        <div className="search-results">
          <SearchBox 
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Search log messages..."
          />
          
          <StatsBar 
            totalLogs={stats.total_logs}
            queryTime={stats.query_time_ms}
            filterCount={Object.keys(selectedFilters).length}
          />

          {loading && <div className="loading">🔄 Searching...</div>}
          {error && <div className="error">{error}</div>}
          
          {searchResults && !loading && (
            <SearchResults 
              results={searchResults}
              selectedFilters={selectedFilters}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
