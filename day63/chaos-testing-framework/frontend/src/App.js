import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import ChaosControlPanel from './components/ChaosControlPanel';
import MetricsDashboard from './components/MetricsDashboard';
import ScenarioList from './components/ScenarioList';
import RecoveryStatus from './components/RecoveryStatus';
// Using native WebSocket instead of Socket.IO

// Google Cloud Skills Boost inspired theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1a73e8',
    },
    secondary: {
      main: '#34a853',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  const [metrics, setMetrics] = useState({});
  const [scenarios, setScenarios] = useState([]);
  const [socket, setSocket] = useState(null);
  const [recoveryStatus, setRecoveryStatus] = useState(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = new WebSocket('ws://localhost:8000/ws');
    setSocket(ws);

    ws.onopen = () => {
      console.log('Connected to chaos testing backend');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      switch(data.type) {
        case 'periodic_update':
          setMetrics(data.metrics || {});
          setScenarios(data.scenarios || []);
          break;
        case 'scenario_started':
          console.log('Scenario started:', data);
          break;
        case 'scenario_stopped':
          console.log('Scenario stopped:', data);
          break;
        case 'recovery_validation_completed':
          setRecoveryStatus(data.report);
          break;
        case 'emergency_stop_completed':
          setScenarios([]);
          console.log('Emergency stop completed');
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🌪️ Chaos Testing Framework - Distributed Log Processing
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Day 63: Building System Resilience
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
        <Box sx={{ display: 'grid', gap: 3 }}>
          {/* Metrics Dashboard */}
          <MetricsDashboard metrics={metrics} />
          
          {/* Main Control Panel */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
            gap: 3 
          }}>
            <ChaosControlPanel socket={socket} />
            <ScenarioList scenarios={scenarios} socket={socket} />
          </Box>
          
          {/* Recovery Status */}
          {recoveryStatus && (
            <RecoveryStatus report={recoveryStatus} />
          )}
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
