import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Box,
  Alert,
  Slider,
  Chip
} from '@mui/material';
import ApiService from '../services/api';

const ChaosControlPanel = ({ socket }) => {
  const [scenarioTemplates, setScenarioTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedTarget, setSelectedTarget] = useState('');
  const [duration, setDuration] = useState(300);
  const [severity, setSeverity] = useState(3);
  const [parameters, setParameters] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    loadScenarioTemplates();
  }, []);

  const loadScenarioTemplates = async () => {
    try {
      const response = await ApiService.getScenarioTemplates();
      setScenarioTemplates(response.templates);
    } catch (error) {
      console.error('Error loading scenario templates:', error);
    }
  };

  const handleTemplateChange = (templateId) => {
    setSelectedTemplate(templateId);
    const template = scenarioTemplates.find(t => t.id === templateId);
    if (template) {
      setParameters(template.parameters);
      setSelectedTarget('');
    }
  };

  const startChaosScenario = async () => {
    if (!selectedTemplate || !selectedTarget) {
      setMessage({ type: 'error', text: 'Please select a scenario template and target' });
      return;
    }

    setLoading(true);
    try {
      const template = scenarioTemplates.find(t => t.id === selectedTemplate);
      
      const scenarioData = {
        type: template.type,
        target: selectedTarget,
        parameters: {
          ...parameters,
          blast_radius: severity * 0.05 // Convert severity to blast radius
        },
        duration,
        severity
      };

      const response = await ApiService.createChaosScenario(scenarioData);
      
      if (response.success) {
        setMessage({
          type: 'success',
          text: `Chaos scenario started successfully! ID: ${response.scenario_id}`
        });
        
        // Reset form
        setSelectedTemplate('');
        setSelectedTarget('');
        setParameters({});
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Failed to start chaos scenario: ${error.response?.data?.detail || error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const emergencyStop = async () => {
    setLoading(true);
    try {
      const response = await ApiService.emergencyStop();
      if (response.success) {
        setMessage({
          type: 'warning',
          text: 'Emergency stop completed - all chaos scenarios stopped'
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Emergency stop failed: ${error.response?.data?.detail || error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const selectedTemplateData = scenarioTemplates.find(t => t.id === selectedTemplate);

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        🌪️ Chaos Control Panel
      </Typography>

      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 2 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Scenario Template Selection */}
        <FormControl fullWidth>
          <InputLabel>Chaos Scenario Type</InputLabel>
          <Select
            value={selectedTemplate}
            onChange={(e) => handleTemplateChange(e.target.value)}
            label="Chaos Scenario Type"
          >
            {scenarioTemplates.map((template) => (
              <MenuItem key={template.id} value={template.id}>
                {template.name} - {template.description}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Target Selection */}
        {selectedTemplateData && (
          <FormControl fullWidth>
            <InputLabel>Target Service</InputLabel>
            <Select
              value={selectedTarget}
              onChange={(e) => setSelectedTarget(e.target.value)}
              label="Target Service"
            >
              {selectedTemplateData.targets.map((target) => (
                <MenuItem key={target} value={target}>
                  {target}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        {/* Duration */}
        <TextField
          label="Duration (seconds)"
          type="number"
          value={duration}
          onChange={(e) => setDuration(parseInt(e.target.value))}
          inputProps={{ min: 30, max: 1800 }}
          fullWidth
        />

        {/* Severity */}
        <Box>
          <Typography gutterBottom>
            Severity Level: {severity}
          </Typography>
          <Slider
            value={severity}
            onChange={(e, value) => setSeverity(value)}
            min={1}
            max={5}
            marks
            step={1}
            valueLabelDisplay="auto"
          />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Chip label="Low Impact" size="small" color="success" />
            <Chip label="High Impact" size="small" color="error" />
          </Box>
        </Box>

        {/* Parameter Configuration */}
        {selectedTemplateData && Object.keys(parameters).length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Scenario Parameters:
            </Typography>
            {Object.entries(parameters).map(([key, value]) => (
              <TextField
                key={key}
                label={key.replace('_', ' ').toUpperCase()}
                value={value}
                onChange={(e) => setParameters({
                  ...parameters,
                  [key]: e.target.value
                })}
                size="small"
                sx={{ mr: 1, mb: 1 }}
              />
            ))}
          </Box>
        )}

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
          <Button
            variant="contained"
            color="warning"
            onClick={startChaosScenario}
            disabled={loading || !selectedTemplate || !selectedTarget}
            sx={{ flex: 1 }}
          >
            {loading ? 'Starting...' : 'Start Chaos Scenario'}
          </Button>
          
          <Button
            variant="outlined"
            color="error"
            onClick={emergencyStop}
            disabled={loading}
          >
            Emergency Stop
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChaosControlPanel;
