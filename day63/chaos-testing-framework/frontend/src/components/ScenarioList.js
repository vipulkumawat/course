import React, { useState } from 'react';
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Button,
  Chip,
  Box,
  Alert
} from '@mui/material';
import axios from 'axios';

const ScenarioList = ({ scenarios, socket }) => {
  const [loading, setLoading] = useState({});

  const stopScenario = async (scenarioId) => {
    setLoading({ ...loading, [scenarioId]: true });
    try {
      const response = await axios.post(`/api/chaos/scenarios/${scenarioId}/stop`);
      if (response.data.success) {
        console.log(`Scenario ${scenarioId} stopped successfully`);
      }
    } catch (error) {
      console.error(`Error stopping scenario ${scenarioId}:`, error);
    } finally {
      setLoading({ ...loading, [scenarioId]: false });
    }
  };

  const validateRecovery = async (scenarioId) => {
    try {
      const response = await axios.post(`/api/recovery/validate/${scenarioId}`);
      if (response.data.success) {
        console.log(`Recovery validation started for ${scenarioId}`);
      }
    } catch (error) {
      console.error(`Error starting recovery validation:`, error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'error';
      case 'pending': return 'warning';
      case 'recovered': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatDuration = (startTime, elapsed) => {
    const minutes = Math.floor(elapsed / 60);
    const seconds = Math.floor(elapsed % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        📋 Active Chaos Scenarios
      </Typography>

      {scenarios.length === 0 ? (
        <Alert severity="info">
          No active chaos scenarios. Use the control panel to start one.
        </Alert>
      ) : (
        <List>
          {scenarios.map((scenario) => (
            <ListItem
              key={scenario.id}
              sx={{
                border: '1px solid #e0e0e0',
                borderRadius: 1,
                mb: 1,
                backgroundColor: scenario.status === 'active' ? '#fff3e0' : '#f5f5f5'
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {scenario.type.replace('_', ' ').toUpperCase()}
                    </Typography>
                    <Chip
                      label={scenario.status}
                      color={getStatusColor(scenario.status)}
                      size="small"
                    />
                  </Box>
                }
                secondary={
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Target:</strong> {scenario.target}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Duration:</strong> {formatDuration(scenario.started_at, scenario.elapsed)} / {Math.floor(scenario.duration / 60)}:00
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      <strong>Severity:</strong> {scenario.severity}/5
                    </Typography>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {scenario.status === 'active' && (
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      onClick={() => stopScenario(scenario.id)}
                      disabled={loading[scenario.id]}
                    >
                      {loading[scenario.id] ? 'Stopping...' : 'Stop'}
                    </Button>
                  )}
                  {scenario.status === 'recovered' && (
                    <Button
                      variant="outlined"
                      color="primary"
                      size="small"
                      onClick={() => validateRecovery(scenario.id)}
                    >
                      Validate Recovery
                    </Button>
                  )}
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default ScenarioList;
