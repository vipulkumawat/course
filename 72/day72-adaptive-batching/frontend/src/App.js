import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  AppBar,
  Toolbar,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Alert,
  LinearProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import axios from 'axios';
import './App.css';

function App() {
  const [metrics, setMetrics] = useState({});
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [loadSimulation, setLoadSimulation] = useState({
    messages_per_second: 100,
    burst_probability: 0.1,
    burst_multiplier: 5
  });
  const [simulationActive, setSimulationActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  const connectWebSocket = () => {
    try {
      const newSocket = new WebSocket('ws://localhost:8000/ws/metrics');

      newSocket.onopen = () => {
        console.log('Connected to WebSocket');
        setIsConnected(true);
        setConnectionAttempts(0);
      };

      newSocket.onclose = () => {
        console.log('Disconnected from WebSocket');
        setIsConnected(false);
        
        // Retry connection after 3 seconds
        setTimeout(() => {
          if (connectionAttempts < 5) {
            console.log(`Retrying WebSocket connection (attempt ${connectionAttempts + 1})`);
            setConnectionAttempts(prev => prev + 1);
            connectWebSocket();
          }
        }, 3000);
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      // Listen for metrics updates
      newSocket.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          setMetrics(parsedData.metrics || {});
          setLastUpdate(new Date());
          
          // Update metrics history for charts
          setMetricsHistory(prev => {
            const newHistory = [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              throughput: parsedData.metrics?.processing?.throughput || 0,
              batchSize: parsedData.metrics?.batching?.current_batch_size_target || 0,
              latency: parsedData.metrics?.processing?.processing_time || 0,
              cpuUsage: parsedData.metrics?.system?.cpu_usage || 0,
              memoryUsage: parsedData.metrics?.system?.memory_usage || 0,
              queueDepth: parsedData.metrics?.batching?.queue_depth || 0,
              errorRate: parsedData.metrics?.processing?.error_rate || 0,
              stabilityScore: parsedData.metrics?.optimization?.current_state?.stability_score || 0
            }];
            
            // Keep only last 50 data points
            return newHistory.slice(-50);
          });
        } catch (error) {
          console.error('Error parsing WebSocket data:', error);
        }
      };

      setSocket(newSocket);
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  };

  useEffect(() => {
    // Wait a bit for backend to be ready, then connect
    const timer = setTimeout(() => {
      connectWebSocket();
    }, 2000);

    return () => {
      clearTimeout(timer);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, []);

  const startLoadSimulation = async () => {
    try {
      await axios.post('/api/simulate-load', loadSimulation);
      setSimulationActive(true);
    } catch (error) {
      console.error('Error starting load simulation:', error);
    }
  };

  const stopLoadSimulation = async () => {
    try {
      await axios.post('/api/simulate-load', { messages_per_second: 0 });
      setSimulationActive(false);
    } catch (error) {
      console.error('Error stopping load simulation:', error);
    }
  };

  const getStatusColor = (value, threshold) => {
    if (value > threshold * 0.9) return 'error';
    if (value > threshold * 0.7) return 'warning';
    return 'success';
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatPercentage = (value) => {
    return `${(value || 0).toFixed(1)}%`;
  };

  const getMetricValue = (path, defaultValue = 0) => {
    return path.split('.').reduce((obj, key) => obj?.[key], metrics) ?? defaultValue;
  };

  return (
    <div className="App">
      <AppBar position="static" sx={{ bgcolor: '#1976d2' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Adaptive Batching System Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={isConnected ? "Connected" : connectionAttempts > 0 ? `Retrying (${connectionAttempts})` : "Disconnected"} 
              color={isConnected ? "success" : "error"} 
              variant="outlined"
              sx={{ color: 'white', borderColor: 'white' }}
            />
            {lastUpdate && (
              <Typography variant="caption" sx={{ color: 'white' }}>
                Last Update: {lastUpdate.toLocaleTimeString()}
              </Typography>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
        {/* System Status Overview */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Alert 
              severity={simulationActive ? "info" : "warning"}
              sx={{ mb: 2 }}
            >
              {simulationActive 
                ? `Load simulation active: ${getMetricValue('batching.simulation_config.messages_per_second', 0)} msg/s`
                : "No load simulation active"
              }
            </Alert>
          </Grid>
        </Grid>

        {/* Key Performance Metrics */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: '#e3f2fd' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Current Batch Size
                </Typography>
                <Typography variant="h4" component="div">
                  {getMetricValue('batching.current_batch_size_target', 0)}
                </Typography>
                <Typography variant="body2">
                  messages per batch
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(getMetricValue('batching.current_batch_size_target', 0) / 5000) * 100}
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: '#e8f5e8' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Throughput
                </Typography>
                <Typography variant="h4" component="div">
                  {(getMetricValue('processing.throughput', 0)).toFixed(1)}
                </Typography>
                <Typography variant="body2">
                  messages/second
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Best: {(getMetricValue('optimization.performance.best_throughput', 0)).toFixed(1)} msg/s
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: '#fff3e0' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Processing Latency
                </Typography>
                <Typography variant="h4" component="div">
                  {((getMetricValue('processing.processing_time', 0)) * 1000).toFixed(0)}
                </Typography>
                <Typography variant="body2">
                  milliseconds
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Target: {getMetricValue('optimization.configuration.target_latency_ms', 1000)}ms
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ bgcolor: '#fce4ec' }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Processed
                </Typography>
                <Typography variant="h4" component="div">
                  {getMetricValue('batching.total_processed', 0).toLocaleString()}
                </Typography>
                <Typography variant="body2">
                  messages
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Errors: {getMetricValue('batching.total_errors', 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* System Resources */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                System Resources
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    CPU Usage
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(getMetricValue('system.cpu_usage', 0))}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={getMetricValue('system.cpu_usage', 0)}
                    color={getStatusColor(getMetricValue('system.cpu_usage', 0), 90)}
                    sx={{ mt: 1 }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Memory Usage
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(getMetricValue('system.memory_usage', 0))}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={getMetricValue('system.memory_usage', 0)}
                    color={getStatusColor(getMetricValue('system.memory_usage', 0), 80)}
                    sx={{ mt: 1 }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Available Memory
                  </Typography>
                  <Typography variant="h6">
                    {formatBytes(getMetricValue('system.memory_available', 0) * 1024 * 1024)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Queue Depth
                  </Typography>
                  <Typography variant="h6">
                    {getMetricValue('batching.queue_depth', 0)}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Optimization Status
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Stability Score
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(getMetricValue('optimization.current_state.stability_score', 0) * 100)}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={getMetricValue('optimization.current_state.stability_score', 0) * 100}
                    sx={{ mt: 1 }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Adjustments Made
                  </Typography>
                  <Typography variant="h6">
                    {getMetricValue('optimization.current_state.adjustment_count', 0)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Improvement
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(getMetricValue('optimization.performance.improvement_percentage', 0))}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Best Batch Size
                  </Typography>
                  <Typography variant="h6">
                    {getMetricValue('optimization.performance.best_batch_size', 'N/A')}
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>

        {/* Load Simulation Control */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Load Simulation Control
              </Typography>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Messages/Second"
                    type="number"
                    value={loadSimulation.messages_per_second}
                    onChange={(e) => setLoadSimulation(prev => ({
                      ...prev,
                      messages_per_second: parseInt(e.target.value) || 0
                    }))}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Burst Probability"
                    type="number"
                    inputProps={{ step: 0.1, min: 0, max: 1 }}
                    value={loadSimulation.burst_probability}
                    onChange={(e) => setLoadSimulation(prev => ({
                      ...prev,
                      burst_probability: parseFloat(e.target.value) || 0
                    }))}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Burst Multiplier"
                    type="number"
                    value={loadSimulation.burst_multiplier}
                    onChange={(e) => setLoadSimulation(prev => ({
                      ...prev,
                      burst_multiplier: parseInt(e.target.value) || 1
                    }))}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  {!simulationActive ? (
                    <Button
                      fullWidth
                      variant="contained"
                      color="primary"
                      onClick={startLoadSimulation}
                    >
                      Start Simulation
                    </Button>
                  ) : (
                    <Button
                      fullWidth
                      variant="contained"
                      color="secondary"
                      onClick={stopLoadSimulation}
                    >
                      Stop Simulation
                    </Button>
                  )}
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>

        {/* Real-time Charts */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Throughput vs Batch Size
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={metricsHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="throughput"
                    stroke="#2196f3"
                    strokeWidth={2}
                    name="Throughput (msg/s)"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="batchSize"
                    stroke="#ff9800"
                    strokeWidth={2}
                    name="Batch Size"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                System Resource Usage
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={metricsHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="cpuUsage"
                    stackId="1"
                    stroke="#4caf50"
                    fill="#4caf50"
                    name="CPU Usage (%)"
                  />
                  <Area
                    type="monotone"
                    dataKey="memoryUsage"
                    stackId="2"
                    stroke="#f44336"
                    fill="#f44336"
                    name="Memory Usage (%)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Processing Latency Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={metricsHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="latency"
                    fill="#9c27b0"
                    name="Latency (seconds)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Queue Depth & Error Rate
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={metricsHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="queueDepth"
                    stroke="#2196f3"
                    strokeWidth={2}
                    name="Queue Depth"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="errorRate"
                    stroke="#f44336"
                    strokeWidth={2}
                    name="Error Rate"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>
        </Grid>

        {/* Detailed Metrics Table */}
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Detailed System Metrics
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell>Value</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>Current Batch Size</TableCell>
                      <TableCell>{getMetricValue('batching.current_batch_size_target', 0)}</TableCell>
                      <TableCell>
                        <Chip 
                          label="Active" 
                          color="success" 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Queue Depth</TableCell>
                      <TableCell>{getMetricValue('batching.queue_depth', 0)}</TableCell>
                      <TableCell>
                        <Chip 
                          label={getMetricValue('batching.queue_depth', 0) > 100 ? "High" : "Normal"} 
                          color={getMetricValue('batching.queue_depth', 0) > 100 ? "warning" : "success"} 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Processed</TableCell>
                      <TableCell>{getMetricValue('batching.total_processed', 0).toLocaleString()}</TableCell>
                      <TableCell>
                        <Chip 
                          label="Running" 
                          color="info" 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Total Errors</TableCell>
                      <TableCell>{getMetricValue('batching.total_errors', 0)}</TableCell>
                      <TableCell>
                        <Chip 
                          label={getMetricValue('batching.total_errors', 0) > 0 ? "Issues" : "Clean"} 
                          color={getMetricValue('batching.total_errors', 0) > 0 ? "error" : "success"} 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Average Processing Time</TableCell>
                      <TableCell>{(getMetricValue('batching.avg_processing_time', 0) * 1000).toFixed(2)}ms</TableCell>
                      <TableCell>
                        <Chip 
                          label="Normal" 
                          color="success" 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Stability Score</TableCell>
                      <TableCell>{formatPercentage(getMetricValue('optimization.current_state.stability_score', 0) * 100)}</TableCell>
                      <TableCell>
                        <Chip 
                          label={getMetricValue('optimization.current_state.stability_score', 0) > 0.8 ? "Stable" : "Unstable"} 
                          color={getMetricValue('optimization.current_state.stability_score', 0) > 0.8 ? "success" : "warning"} 
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}

export default App;
