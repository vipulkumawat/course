import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Box, Alert } from '@mui/material';
import { TrendingUp, Storage, AttachMoney, Timeline } from '@mui/icons-material';
import ForecastChart from './components/ForecastChart';
import CostAnalysis from './components/CostAnalysis';
import MetricsCard from './components/MetricsCard';
import './App.css';

function App() {
  const [summary, setSummary] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      // Fetch summary data
      const summaryResponse = await fetch('http://localhost:8000/api/dashboard/summary');
      const summaryData = await summaryResponse.json();
      
      if (summaryData.status === 'success') {
        setSummary(summaryData.data);
      }

      // Fetch forecast data
      const forecastResponse = await fetch('http://localhost:8000/api/forecast/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ horizon_days: 30 })
      });
      const forecastResult = await forecastResponse.json();
      
      if (forecastResult.status === 'success') {
        setForecastData(forecastResult);
      }

      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <Typography>Loading storage forecasting dashboard...</Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error">Error loading data: {error}</Alert>
      </Container>
    );
  }

  return (
    <div className="App" style={{ background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)', minHeight: '100vh', paddingTop: '20px' }}>
      <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#6366f1', fontWeight: 'bold' }}>
          Storage Usage Forecasting Dashboard
        </Typography>
        
        {/* Key Metrics Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricsCard
              title="Current Usage"
              value={`${summary?.current_usage_gb || 0} GB`}
              icon={<Storage />}
              color="#2196f3"
              subtitle={`${summary?.utilization_percent || 0}% utilized`}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricsCard
              title="30-Day Forecast"
              value={`${summary?.predicted_usage_30d_gb || 0} GB`}
              icon={<TrendingUp />}
              color="#4caf50"
              subtitle={`${summary?.growth_rate_percent || 0}% growth`}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricsCard
              title="Current Cost"
              value={`$${summary?.current_monthly_cost || 0}`}
              icon={<AttachMoney />}
              color="#ff9800"
              subtitle="Per month"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricsCard
              title="Forecast Accuracy"
              value={`${summary?.forecast_accuracy || 0}%`}
              icon={<Timeline />}
              color="#9c27b0"
              subtitle={summary?.recommendation || 'Monitor'}
            />
          </Grid>
        </Grid>

        {/* Forecast Chart */}
        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 3, height: '400px' }}>
              <Typography variant="h6" gutterBottom>
                Storage Usage Forecast (30 Days)
              </Typography>
              {forecastData && <ForecastChart data={forecastData} />}
            </Paper>
          </Grid>
          
          <Grid item xs={12} lg={4}>
            <Paper sx={{ p: 3, height: '400px' }}>
              <Typography variant="h6" gutterBottom>
                Cost Analysis
              </Typography>
              {forecastData && <CostAnalysis data={forecastData} />}
            </Paper>
          </Grid>
        </Grid>

        {/* Recommendations */}
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recommendations
              </Typography>
              <Box sx={{ mt: 2 }}>
                {forecastData?.recommendation && (
                  <Alert 
                    severity={forecastData.recommendation.risk_level === 'high' ? 'warning' : 'info'}
                    sx={{ mb: 2 }}
                  >
                    <strong>{forecastData.recommendation.action}</strong> - {forecastData.recommendation.timeline}
                  </Alert>
                )}
                <Typography variant="body2" color="text.secondary">
                  Model Used: {forecastData?.forecast?.best_model || 'Ensemble'} | 
                  Accuracy: {summary?.forecast_accuracy || 0}% |
                  Last Updated: {new Date(summary?.last_updated || Date.now()).toLocaleString()}
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}

export default App;
