// Utility functions for formatting data in the UI

export const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatPercentage = (value, decimals = 1) => {
  return `${value.toFixed(decimals)}%`;
};

export const formatLatency = (ms) => {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`;
  } else {
    return `${(ms / 1000).toFixed(1)}s`;
  }
};

export const formatTimestamp = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleString();
};

export const getStatusColor = (status) => {
  const colors = {
    'active': 'error',
    'pending': 'warning',
    'completed': 'success',
    'failed': 'error',
    'recovered': 'success',
    'timeout': 'warning'
  };
  return colors[status] || 'default';
};

export const getSeverityLabel = (severity) => {
  const labels = {
    1: 'Very Low',
    2: 'Low',
    3: 'Medium',
    4: 'High',
    5: 'Very High'
  };
  return labels[severity] || 'Unknown';
};

export const getSeverityColor = (severity) => {
  const colors = {
    1: 'success',
    2: 'info',
    3: 'warning',
    4: 'error',
    5: 'error'
  };
  return colors[severity] || 'default';
};
