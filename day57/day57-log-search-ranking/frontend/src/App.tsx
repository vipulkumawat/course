import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, Box, Typography, AppBar, Toolbar } from '@mui/material';
import SearchInterface from './components/Search/SearchInterface';
import './App.css';

// Google Cloud Skills Boost inspired theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Google Blue
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#f57c00', // Google Orange
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Google Sans", "Roboto", "Arial", sans-serif',
    h4: {
      fontWeight: 500,
    },
    h6: {
      fontWeight: 400,
    },
  },
  shape: {
    borderRadius: 8,
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" elevation={0} sx={{ borderBottom: '1px solid #e0e0e0' }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 500 }}>
              Day 57: Log Search with Intelligent Ranking
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.7)' }}>
              Distributed Log Processing System
            </Typography>
          </Toolbar>
        </AppBar>
        
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
          <Box sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: 2,
            p: 4,
            mb: 4,
            color: 'white'
          }}>
            <Typography variant="h4" gutterBottom>
              Intelligent Log Search System
            </Typography>
            <Typography variant="body1">
              Search logs with TF-IDF ranking, contextual relevance scoring, and real-time suggestions
            </Typography>
          </Box>
          
          <SearchInterface />
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
