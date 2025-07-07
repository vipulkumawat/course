import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Chip,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import FilterListIcon from '@mui/icons-material/FilterList';
import { searchLogs, getSearchSuggestions, getSearchStats } from '../../services/searchService';

interface SearchContext {
  mode: string;
  user_focus: string;
}

interface SearchResult {
  id: string;
  message: string;
  timestamp: string;
  level: string;
  service: string;
  relevance_score: number;
  final_relevance_score: number;
  score_components: {
    tfidf_score: number;
    temporal_relevance: number;
    severity_boost: number;
    service_authority: number;
    user_context: number;
  };
  ranking_explanation: string;
}

const SearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [context, setContext] = useState<SearchContext>({
    mode: 'normal',
    user_focus: ''
  });
  const [executionTime, setExecutionTime] = useState<number>(0);

  // Sample search queries for demonstration
  const sampleQueries = [
    'authentication error',
    'payment timeout',
    'database connection',
    'user session',
    'api response time',
    'memory usage high'
  ];

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await searchLogs({
        query: query,
        context: context,
        limit: 20
      });

      setResults(response.results);
      setExecutionTime(response.execution_time_ms);
    } catch (err) {
      setError('Search failed. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    handleSearch();
  };

  return (
    <Box sx={{ mt: 3 }}>
      {/* Search Input */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={8}>
            <Autocomplete
              freeSolo
              options={sampleQueries}
              value={query}
              onChange={(_, newValue) => setQuery(newValue || '')}
              onInputChange={(_, newInputValue) => setQuery(newInputValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  fullWidth
                  label="Search logs..."
                  variant="outlined"
                  placeholder="Enter search query (e.g., 'authentication error')"
                  disabled={loading}
                />
              )}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              disabled={loading || !query.trim()}
              sx={{ height: 56 }}
            >
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </Grid>
        </Grid>

        {/* Search Context */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Search Context
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Search Mode</InputLabel>
                <Select
                  value={context.mode}
                  onChange={(e) => setContext({ ...context, mode: e.target.value })}
                  label="Search Mode"
                >
                  <MenuItem value="normal">Normal Search</MenuItem>
                  <MenuItem value="incident">Incident Investigation</MenuItem>
                  <MenuItem value="performance">Performance Analysis</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                size="small"
                label="User Focus"
                placeholder="e.g., authentication, database, api"
                value={context.user_focus}
                onChange={(e) => setContext({ ...context, user_focus: e.target.value })}
              />
            </Grid>
          </Grid>
        </Box>

        {/* Sample Queries */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Try these sample queries:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {sampleQueries.map((suggestion) => (
              <Chip
                key={suggestion}
                label={suggestion}
                size="small"
                clickable
                onClick={() => handleSuggestionClick(suggestion)}
                variant="outlined"
              />
            ))}
          </Box>
        </Box>
      </Paper>

      {/* Loading Indicator */}
      {loading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
          <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
            Searching logs with intelligent ranking...
          </Typography>
        </Box>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Search Results ({results.length})
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TrendingUpIcon color="primary" />
              <Typography variant="body2" color="text.secondary">
                Execution time: {executionTime}ms
              </Typography>
            </Box>
          </Box>

          <Grid container spacing={2}>
            {results.map((result) => (
              <Grid item xs={12} key={result.id}>
                <Card elevation={1}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {result.message}
                      </Typography>
                      <Chip
                        label={`${(result.final_relevance_score * 100).toFixed(0)}%`}
                        color="primary"
                        size="small"
                      />
                    </Box>
                    
                    <Box sx={{ display: 'flex', gap: 2, mb: 1 }}>
                      <Chip
                        label={result.level}
                        size="small"
                        color={result.level === 'ERROR' ? 'error' : result.level === 'WARN' ? 'warning' : 'default'}
                      />
                      <Chip label={result.service} size="small" variant="outlined" />
                      <Typography variant="caption" color="text.secondary">
                        {new Date(result.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                    
                    <Typography variant="caption" color="text.secondary">
                      <strong>Ranking:</strong> {result.ranking_explanation}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* No Results */}
      {!loading && !error && results.length === 0 && query && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No results found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search terms or search context
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default SearchInterface; 