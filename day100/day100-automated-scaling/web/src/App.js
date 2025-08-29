import React, { useState, useEffect } from 'react';
import { Container, Grid, Paper, Typography, Box } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './App.css';

function App() {
  const [metrics, setMetrics] = useState({});
  const [scalingHistory, setScalingHistory] = useState([]);
  const [systemStatus, setSystemStatus] = useState({});
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'status_update') {
        setSystemStatus(data.status);
        setMetrics(data.metrics);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setSocket(null);
    };

    // Fetch initial data
    fetchMetrics();
    fetchScalingHistory();
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const fetchScalingHistory = async () => {
    try {
      const response = await fetch('/api/scaling-history');
      const data = await response.json();
      setScalingHistory(data);
    } catch (error) {
      console.error('Error fetching scaling history:', error);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  return (
    <div className="App">
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center" color="primary">
          🚀 Automated Scaling Dashboard
        </Typography>
        
        <Grid container spacing={3}>
          {/* System Status */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: 200 }}>
              <Typography variant="h6" gutterBottom>
                System Status
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body1">
                  Status: <strong style={{color: systemStatus.running ? 'green' : 'red'}}>
                    {systemStatus.running ? 'Running' : 'Stopped'}
                  </strong>
                </Typography>
                <Typography variant="body1">
                  Components: <strong>{systemStatus.components || 0}</strong>
                </Typography>
                <Typography variant="body1">
                  Recent Actions: <strong>{systemStatus.recent_scaling_actions || 0}</strong>
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Component Metrics */}
          {Object.entries(metrics).map(([componentId, metric]) => (
            <Grid item xs={12} md={4} key={componentId}>
              <Paper sx={{ p: 2, height: 200 }}>
                <Typography variant="h6" gutterBottom>
                  {componentId}
                </Typography>
                <Box sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    CPU: <strong>{metric.cpu_percent?.toFixed(1)}%</strong>
                  </Typography>
                  <Typography variant="body2">
                    Queue: <strong>{metric.queue_depth || 0}</strong>
                  </Typography>
                  <Typography variant="body2">
                    Instances: <strong>{metric.instance_count || 1}</strong>
                  </Typography>
                  <Typography variant="body2">
                    Throughput: <strong>{metric.throughput_per_sec || 0}/sec</strong>
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          ))}

          {/* CPU Usage Chart */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                CPU Usage by Component
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={Object.entries(metrics).map(([id, m]) => ({
                  name: id.split('-')[0],
                  cpu: m.cpu_percent || 0,
                  instances: m.instance_count || 1
                }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="cpu" stroke="#8884d8" name="CPU %" />
                  <Line type="monotone" dataKey="instances" stroke="#82ca9d" name="Instances" />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Scaling History */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Recent Scaling Actions
              </Typography>
              <Box sx={{ height: 300, overflow: 'auto' }}>
                {scalingHistory.length === 0 ? (
                  <Typography variant="body2" color="textSecondary">
                    No scaling actions yet
                  </Typography>
                ) : (
                  scalingHistory.slice().reverse().map((action, index) => (
                    <Box key={index} sx={{ mb: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                      <Typography variant="body2">
                        <strong>{action.component_id}</strong>: {action.action}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {action.current_instances} → {action.target_instances} instances
                      </Typography>
                      <Typography variant="caption" display="block" color="textSecondary">
                        {formatTimestamp(action.timestamp)} - {action.reason}
                      </Typography>
                    </Box>
                  ))
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}

export default App;
