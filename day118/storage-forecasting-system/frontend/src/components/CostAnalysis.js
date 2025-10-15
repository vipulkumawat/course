import React from 'react';
import { Box, Typography, Chip, Divider } from '@mui/material';
import { TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';

const CostAnalysis = ({ data }) => {
  if (!data || !data.cost_analysis) return <div>No cost data available</div>;

  const cost = data.cost_analysis;
  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return <TrendingUp sx={{ color: '#ef4444' }} />;
      case 'decreasing': return <TrendingDown sx={{ color: '#10b981' }} />;
      default: return <TrendingFlat sx={{ color: '#f59e0b' }} />;
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Total Period Cost
        </Typography>
        <Typography variant="h4" sx={{ color: '#6366f1', fontWeight: 'bold' }}>
          ${Math.round(cost.total_period_cost * 100) / 100}
        </Typography>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Average Monthly Cost
        </Typography>
        <Typography variant="h5" sx={{ color: '#10b981' }}>
          ${Math.round(cost.average_monthly_cost * 100) / 100}
        </Typography>
      </Box>

      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Cost Trend
        </Typography>
        <Box display="flex" alignItems="center">
          {getTrendIcon(cost.cost_trend)}
          <Chip 
            label={cost.cost_trend.charAt(0).toUpperCase() + cost.cost_trend.slice(1)}
            color={cost.cost_trend === 'increasing' ? 'error' : 'success'}
            variant="outlined"
            sx={{ ml: 1 }}
          />
        </Box>
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="subtitle1" gutterBottom>
          Annual Projection
        </Typography>
        <Typography variant="h5" sx={{ color: '#f59e0b' }}>
          ${Math.round(cost.projected_annual_cost * 100) / 100}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Based on current growth patterns
        </Typography>
      </Box>
    </Box>
  );
};

export default CostAnalysis;
