import React from 'react';
import {
  Paper,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert
} from '@mui/material';
import { ExpandMore, CheckCircle, Error, Warning } from '@mui/icons-material';

const RecoveryStatus = ({ report }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'failed':
        return <Error sx={{ color: 'error.main' }} />;
      case 'timeout':
        return <Warning sx={{ color: 'warning.main' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'timeout': return 'warning';
      default: return 'default';
    }
  };

  const successRate = (report.summary.passed_tests / report.summary.total_tests) * 100;

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        🔍 Recovery Validation Report
        <Chip 
          label={report.overall_success ? 'PASSED' : 'FAILED'}
          color={report.overall_success ? 'success' : 'error'}
          sx={{ ml: 2 }}
        />
      </Typography>

      {/* Summary */}
      <Alert 
        severity={report.overall_success ? 'success' : 'error'}
        sx={{ mb: 3 }}
      >
        <Typography variant="subtitle1">
          Recovery validation {report.overall_success ? 'completed successfully' : 'failed'} 
          in {report.validation_duration.toFixed(1)} seconds
        </Typography>
        <Typography variant="body2">
          {report.summary.passed_tests}/{report.summary.total_tests} tests passed 
          ({successRate.toFixed(1)}% success rate)
        </Typography>
      </Alert>

      {/* Progress Bar */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Test Success Rate
        </Typography>
        <LinearProgress 
          variant="determinate" 
          value={successRate}
          color={report.overall_success ? 'success' : 'error'}
          sx={{ height: 10, borderRadius: 1 }}
        />
        <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
          {successRate.toFixed(1)}% ({report.summary.passed_tests}/{report.summary.total_tests})
        </Typography>
      </Box>

      {/* Detailed Test Results */}
      <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
        Detailed Test Results
      </Typography>
      
      {report.test_results.map((test, index) => (
        <Accordion key={index} sx={{ mb: 1 }}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              {getStatusIcon(test.status)}
              <Typography sx={{ flex: 1 }}>
                {test.name.replace('_', ' ').toUpperCase()}
              </Typography>
              <Chip 
                label={test.status} 
                color={getStatusColor(test.status)}
                size="small"
              />
              <Typography variant="body2" color="textSecondary">
                {test.duration.toFixed(2)}s
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              {test.error_message && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {test.error_message}
                </Alert>
              )}
              
              <Typography variant="subtitle2" gutterBottom>
                Test Details:
              </Typography>
              <Box component="pre" sx={{ 
                backgroundColor: '#f5f5f5', 
                p: 2, 
                borderRadius: 1,
                fontSize: '0.8rem',
                overflow: 'auto'
              }}>
                {JSON.stringify(test.details, null, 2)}
              </Box>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Paper>
  );
};

export default RecoveryStatus;
