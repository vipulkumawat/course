import React, { useState, useEffect } from 'react';
import axios from 'axios';
import moment from 'moment';
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
  Bar
} from 'recharts';
import './index.css';

function App() {
  const [predictions, setPredictions] = useState(null);
  const [health, setHealth] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoProgress, setDemoProgress] = useState('');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [predictionsRes, healthRes, metricsRes] = await Promise.all([
        axios.get('/predictions'),
        axios.get('/health'),
        axios.get('/metrics')
      ]);

      setPredictions(predictionsRes.data);
      setHealth(healthRes.data);
      setMetrics(metricsRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const runDemo = async () => {
    setDemoRunning(true);
    setDemoProgress('🚀 Starting demo...');
    
    try {
      // Call the demo endpoint with progress updates
      setDemoProgress('📊 Generating sample log data...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setDemoProgress('🤖 Training forecasting models...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setDemoProgress('🔮 Generating ensemble predictions...');
      const demoResponse = await axios.post('/demo/run');
      
      if (demoResponse.data.status === 'success') {
        setDemoProgress('🔄 Updating dashboard...');
        await fetchData();
        
        setDemoProgress('✅ Demo completed successfully!');
        setTimeout(() => {
          setDemoProgress('');
          setDemoRunning(false);
        }, 2000);
      } else {
        throw new Error('Demo failed to complete');
      }
      
    } catch (err) {
      setDemoProgress('❌ Demo failed: ' + (err.response?.data?.detail || err.message));
      setTimeout(() => {
        setDemoProgress('');
        setDemoRunning(false);
      }, 3000);
    }
  };

  const formatChartData = () => {
    if (!predictions || !predictions.ensemble_prediction) return [];
    
    return predictions.timestamps.map((timestamp, index) => ({
      time: moment(timestamp).format('HH:mm'),
      prediction: predictions.ensemble_prediction[index].toFixed(2),
      confidence: predictions.ensemble_confidence[index].toFixed(3),
      arima: predictions.individual_forecasts.arima?.[index]?.toFixed(2) || 0,
      prophet: predictions.individual_forecasts.prophet?.[index]?.toFixed(2) || 0,
      lstm: predictions.individual_forecasts.lstm?.[index]?.toFixed(2) || 0,
      exponential_smoothing: predictions.individual_forecasts.exponential_smoothing?.[index]?.toFixed(2) || 0
    }));
  };

  const getAlertClass = (level) => {
    switch (level) {
      case 'high': return 'alert-high';
      case 'medium': return 'alert-medium';
      case 'low': return 'alert-low';
      default: return '';
    }
  };

  const getConfidenceClass = (confidence) => {
    if (confidence >= 0.85) return 'confidence-high';
    if (confidence >= 0.65) return 'confidence-medium';
    return 'confidence-low';
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">
          🤖 Loading Predictive Analytics Dashboard...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          ❌ {error}
        </div>
      </div>
    );
  }

  const chartData = formatChartData();
  const avgConfidence = predictions?.ensemble_confidence?.reduce((a, b) => a + b, 0) / (predictions?.ensemble_confidence?.length || 1);

  return (
    <div className="dashboard">
      <div className="header">
        <h1>🔮 Predictive Analytics Dashboard</h1>
        <p>Day 80: Forecasting System Behavior from Log Patterns</p>
        <div className="header-controls">
          <p>
            <span className={`status-indicator ${health?.status === 'healthy' ? 'status-healthy' : 'status-degraded'}`}></span>
            System Status: {health?.status || 'Unknown'}
          </p>
          <button 
            className={`demo-button ${demoRunning ? 'demo-running' : ''}`}
            onClick={runDemo}
            disabled={demoRunning}
          >
            {demoRunning ? '🔄 Running Demo...' : '🎬 Run Demo'}
          </button>
        </div>
        {demoProgress && (
          <div className="demo-progress">
            {demoProgress}
          </div>
        )}
      </div>

      <div className="dashboard-grid">
        {/* System Health Card */}
        <div className="card">
          <h3>🏥 System Health</h3>
          <div className="metrics-grid">
            <div className="metric-item">
              <div className="metric-value">{health?.services?.models_loaded || 0}</div>
              <div className="metric-label">Models Loaded</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{health?.services?.redis || 'Unknown'}</div>
              <div className="metric-label">Redis Status</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{predictions?.alert_level || 'None'}</div>
              <div className="metric-label">Alert Level</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{moment(predictions?.timestamp).format('HH:mm:ss')}</div>
              <div className="metric-label">Last Update</div>
            </div>
          </div>
        </div>

        {/* Prediction Confidence Card */}
        <div className={`card ${getAlertClass(predictions?.alert_level)}`}>
          <h3>🎯 Prediction Confidence</h3>
          <div className="confidence-bar">
            <div 
              className={`confidence-fill ${getConfidenceClass(avgConfidence)}`}
              style={{ width: `${(avgConfidence * 100)}%` }}
            ></div>
          </div>
          <div style={{ textAlign: 'center', marginTop: '10px' }}>
            <strong>{(avgConfidence * 100).toFixed(1)}% Confidence</strong>
          </div>
          <div className="metrics-grid" style={{ marginTop: '15px' }}>
            <div className="metric-item">
              <div className="metric-value">{metrics?.forecast_confidence?.high || 0}</div>
              <div className="metric-label">High Confidence</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{metrics?.forecast_confidence?.medium || 0}</div>
              <div className="metric-label">Medium Confidence</div>
            </div>
            <div className="metric-item">
              <div className="metric-value">{metrics?.forecast_confidence?.low || 0}</div>
              <div className="metric-label">Low Confidence</div>
            </div>
          </div>
        </div>

        {/* Ensemble Forecast Chart */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h3>📈 Ensemble Forecast - Response Time Prediction</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis label={{ value: 'Response Time (ms)', angle: -90, position: 'insideLeft' }} />
                <Tooltip 
                  formatter={(value, name) => [`${value}ms`, name === 'prediction' ? 'Ensemble Prediction' : name]}
                  labelFormatter={(label) => `Time: ${label}`}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="prediction"
                  stroke="#007bff"
                  fill="rgba(0, 123, 255, 0.3)"
                  strokeWidth={3}
                  name="Ensemble Prediction"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Individual Model Predictions */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h3>🧠 Individual Model Predictions</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis label={{ value: 'Response Time (ms)', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => [`${value}ms`]} />
                <Legend />
                <Line type="monotone" dataKey="arima" stroke="#28a745" strokeWidth={2} name="ARIMA" />
                <Line type="monotone" dataKey="prophet" stroke="#007bff" strokeWidth={2} name="Prophet" />
                <Line type="monotone" dataKey="lstm" stroke="#dc3545" strokeWidth={2} name="LSTM" />
                <Line type="monotone" dataKey="exponential_smoothing" stroke="#ffc107" strokeWidth={2} name="Exp. Smoothing" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Performance */}
        <div className="card">
          <h3>⚙️ Model Configuration</h3>
          <div style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
            <div><strong>Active Models:</strong></div>
            <ul style={{ margin: '10px 0', paddingLeft: '20px' }}>
              {health?.services?.models_available?.map(model => (
                <li key={model}>{model.toUpperCase()}</li>
              )) || <li>No models loaded</li>}
            </ul>
            <div><strong>Forecast Horizon:</strong> {predictions?.forecast_horizon_minutes || 0} minutes</div>
            <div><strong>Update Interval:</strong> 5 minutes</div>
            <div><strong>Ensemble Weights:</strong></div>
            <ul style={{ margin: '10px 0', paddingLeft: '20px', fontSize: '0.8rem' }}>
              <li>ARIMA: 25%</li>
              <li>Prophet: 35%</li>
              <li>LSTM: 30%</li>
              <li>Exp. Smoothing: 10%</li>
            </ul>
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="card">
          <h3>📊 Confidence Distribution</h3>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { name: 'High (>85%)', value: metrics?.forecast_confidence?.high || 0, fill: '#28a745' },
                { name: 'Medium (65-85%)', value: metrics?.forecast_confidence?.medium || 0, fill: '#ffc107' },
                { name: 'Low (<65%)', value: metrics?.forecast_confidence?.low || 0, fill: '#dc3545' }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '30px', color: 'white', opacity: '0.8' }}>
        <p>🚀 Day 80: Predictive Analytics for Log Forecasting | Last Updated: {moment().format('YYYY-MM-DD HH:mm:ss')}</p>
      </div>
    </div>
  );
}

export default App;
