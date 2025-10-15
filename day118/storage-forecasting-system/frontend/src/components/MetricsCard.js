import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';

const MetricsCard = ({ title, value, icon, color, subtitle }) => {
  return (
    <Card sx={{ 
      height: '100%', 
      backgroundColor: '#ffffff',
      borderRadius: 2,
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
      border: '1px solid #e2e8f0',
      transition: 'all 0.3s ease-in-out',
      '&:hover': {
        boxShadow: '0 10px 25px rgba(99, 102, 241, 0.15)',
        transform: 'translateY(-2px)',
        borderColor: '#6366f1'
      }
    }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={1}>
          <Box sx={{ color, mr: 1 }}>
            {icon}
          </Box>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold', color: '#1e293b' }}>
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="p" sx={{ color, fontWeight: 'bold', mb: 1 }}>
          {value}
        </Typography>
        <Typography variant="body2" sx={{ color: '#64748b' }}>
          {subtitle}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default MetricsCard;
