import React from 'react';
import { Paper, Typography, Grid, Box, Chip } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MetricCard = ({ title, value, unit, status = 'normal' }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'warning': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#4caf50';
    }
  };

  return (
    <Paper sx={{ p: 2, textAlign: 'center', height: '100%' }}>
      <Typography variant="h6" color="textSecondary" gutterBottom>
        {title}
      </Typography>
      <Typography 
        variant="h4" 
        sx={{ 
          color: getStatusColor(),
          fontWeight: 'bold',
          mb: 1
        }}
      >
        {value}
        <Typography component="span" variant="h6" sx={{ ml: 1 }}>
          {unit}
        </Typography>
      </Typography>
      <Chip 
        label={status.toUpperCase()} 
        size="small" 
        sx={{ 
          backgroundColor: getStatusColor(),
          color: 'white',
          fontWeight: 'bold'
        }} 
      />
    </Paper>
  );
};

const ServiceHealthIndicator = ({ services }) => {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Service Health
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {Object.entries(services || {}).map(([service, healthy]) => (
          <Chip
            key={service}
            label={service}
            color={healthy ? 'success' : 'error'}
            variant={healthy ? 'filled' : 'outlined'}
            sx={{ textTransform: 'capitalize' }}
          />
        ))}
      </Box>
    </Paper>
  );
};

const MetricsDashboard = ({ metrics }) => {
  const getCpuStatus = (usage) => {
    if (usage > 90) return 'critical';
    if (usage > 70) return 'warning';
    return 'normal';
  };

  const getMemoryStatus = (usage) => {
    if (usage > 95) return 'critical';
    if (usage > 80) return 'warning';
    return 'normal';
  };

  const getLatencyStatus = (latency) => {
    if (latency > 500) return 'critical';
    if (latency > 100) return 'warning';
    return 'normal';
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 500 }}>
        📊 Real-time System Metrics
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Metrics */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="CPU Usage"
            value={metrics.cpu_usage?.toFixed(1) || '0'}
            unit="%"
            status={getCpuStatus(metrics.cpu_usage || 0)}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Memory Usage"
            value={metrics.memory_usage?.toFixed(1) || '0'}
            unit="%"
            status={getMemoryStatus(metrics.memory_usage || 0)}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Network Latency"
            value={metrics.network_latency?.toFixed(0) || '0'}
            unit="ms"
            status={getLatencyStatus(metrics.network_latency || 0)}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Log Processing Rate"
            value={metrics.custom_metrics?.log_processing_rate?.toFixed(0) || '0'}
            unit="logs/sec"
            status="normal"
          />
        </Grid>
        
        {/* Service Health */}
        <Grid item xs={12} md={6}>
          <ServiceHealthIndicator services={metrics.service_health} />
        </Grid>
        
        {/* Custom Metrics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Application Metrics
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Queue Depth:</Typography>
                <Typography fontWeight="bold">
                  {metrics.custom_metrics?.message_queue_depth || 0}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Error Rate:</Typography>
                <Typography fontWeight="bold">
                  {(metrics.custom_metrics?.error_rate || 0).toFixed(2)}%
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MetricsDashboard;
