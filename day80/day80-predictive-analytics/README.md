# 🔮 Day 80: Predictive Analytics System

A comprehensive predictive analytics system that forecasts system behavior from log patterns using ensemble machine learning models.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11**
- **Node.js** (v16 or higher)
- **npm** (comes with Node.js)
- **Redis** (for caching and background tasks)

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd day80-predictive-analytics
   ```

2. **Start the system**:
   ```bash
   ./start.sh
   ```

3. **Access the dashboard**:
   - Open http://localhost:3000 in your browser
   - Click the **🎬 Run Demo** button to see the system in action

4. **Stop the system**:
   ```bash
   ./stop.sh
   ```

## 📋 Available Scripts

### `./start.sh` - Start the System
- ✅ Checks all prerequisites
- ✅ Creates virtual environment if needed
- ✅ Installs dependencies
- ✅ Starts Redis server
- ✅ Starts Celery background services
- ✅ Generates sample data and trains models
- ✅ Starts API server (port 8080)
- ✅ Starts dashboard (port 3000)
- ✅ Waits for services to be ready
- ✅ Provides detailed status information

### `./stop.sh` - Stop the System
- ✅ Gracefully stops all services
- ✅ Kills processes if needed
- ✅ Cleans up PID files
- ✅ Deactivates virtual environment
- ✅ Provides detailed status information

### `./build_and_start.sh` - Build, Test, and Start
- ✅ Runs all tests
- ✅ Generates sample data
- ✅ Trains models
- ✅ Tests API endpoints
- ✅ Starts the complete system
- ✅ Perfect for development and testing

## 🎬 Demo Functionality

The system includes a **demo button** on the dashboard that demonstrates the full predictive analytics pipeline:

1. **📊 Generate Sample Data**: Creates realistic log data
2. **🤖 Train Models**: Trains ARIMA, Prophet, and Exponential Smoothing models
3. **🔮 Generate Predictions**: Creates ensemble forecasts
4. **🔄 Update Dashboard**: Refreshes all charts and metrics

### How to Use the Demo

1. Open http://localhost:3000
2. Click the **🎬 Run Demo** button in the header
3. Watch the progress messages
4. View the updated dashboard with real predictions

## 🏗️ System Architecture

### Backend (Python/FastAPI)
- **API Server**: FastAPI on port 8080
- **Models**: ARIMA, Prophet, Exponential Smoothing
- **Background Tasks**: Celery with Redis
- **Data Storage**: CSV files + Redis caching

### Frontend (React)
- **Dashboard**: React app on port 3000
- **Charts**: Recharts for data visualization
- **Real-time Updates**: 30-second refresh intervals
- **Proxy**: Forwards API calls to backend

### Services
- **Redis**: Caching and message broker
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task execution

## 📊 Features

### Predictive Models
- **ARIMA**: Time series forecasting
- **Prophet**: Trend analysis and seasonality
- **Exponential Smoothing**: Simple forecasting
- **Ensemble**: Combines all models for better accuracy

### Dashboard Features
- **Real-time Predictions**: 60-minute forecast horizon
- **Individual Model Views**: See how each model predicts
- **Confidence Levels**: High/Medium/Low confidence indicators
- **System Health**: Service status and metrics
- **Interactive Charts**: Zoom, hover, and explore data

### API Endpoints
- `GET /health` - System health check
- `GET /predictions` - Latest ensemble predictions
- `GET /metrics` - System metrics and performance
- `POST /demo/run` - Run the demo pipeline
- `GET /forecast/{steps}` - Generate custom forecasts

## 🔧 Configuration

### Model Configuration (`config/config.py`)
```python
# Forecasting parameters
forecast_horizon_minutes: int = 60
update_interval_minutes: int = 5

# Model weights
ensemble_weights: Dict[str, float] = {
    "arima": 0.35,
    "prophet": 0.45, 
    "exponential_smoothing": 0.20
}
```

### API Configuration
- **Host**: localhost
- **Port**: 8080
- **CORS**: Enabled for all origins

### Frontend Configuration
- **Port**: 3000
- **Proxy**: http://localhost:8080
- **Refresh Interval**: 30 seconds

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_api.py -v

# Run with coverage
python -m pytest tests/ --cov=src
```

## 📁 Project Structure

```
day80-predictive-analytics/
├── src/
│   ├── api/           # FastAPI application
│   ├── models/        # ML models (ARIMA, Prophet, etc.)
│   ├── forecasting/   # Forecasting engine
│   └── utils/         # Data utilities
├── frontend/          # React dashboard
├── tests/             # Test suite
├── data/              # Generated data files
├── models/trained/    # Trained model files
├── config/            # Configuration files
├── start.sh           # Start script
├── stop.sh            # Stop script
├── build_and_start.sh # Build and start script
└── requirements.txt   # Python dependencies
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8080
   lsof -i :3000
   
   # Kill the process
   kill -9 <PID>
   ```

2. **Redis Connection Issues**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Start Redis manually
   redis-server --daemonize yes --port 6379
   ```

3. **Python Path Issues**
   ```bash
   # Set PYTHONPATH manually
   export PYTHONPATH="$(pwd)"
   ```

4. **Node.js Dependencies**
   ```bash
   # Reinstall frontend dependencies
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### Logs and Debugging

- **API Logs**: Check terminal output when running `./start.sh`
- **Frontend Logs**: Check browser console (F12)
- **Redis Logs**: Check Redis server output
- **Celery Logs**: Check Celery worker output

## 🚀 Deployment

### Production Setup

1. **Environment Variables**:
   ```bash
   export PYTHONPATH="/path/to/project"
   export REDIS_URL="redis://localhost:6379/0"
   ```

2. **Process Management**:
   ```bash
   # Use PM2 for Node.js processes
   npm install -g pm2
   pm2 start frontend/package.json
   
   # Use systemd for Python processes
   sudo systemctl enable redis
   sudo systemctl start redis
   ```

3. **Reverse Proxy**:
   ```nginx
   # Nginx configuration
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api/ {
           proxy_pass http://localhost:8080/;
       }
   }
   ```

## 📈 Performance

### Benchmarks
- **Data Generation**: ~4000 samples in 2-3 seconds
- **Model Training**: ~10-15 seconds for all models
- **Prediction Generation**: ~1-2 seconds
- **Dashboard Load Time**: ~2-3 seconds

### Optimization Tips
- Use Redis for caching predictions
- Implement model versioning
- Add data compression for large datasets
- Use async/await for I/O operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Roadmap

- [ ] Add LSTM model support
- [ ] Implement real-time data streaming
- [ ] Add more visualization options
- [ ] Support for multiple data sources
- [ ] Model performance monitoring
- [ ] Automated model retraining
- [ ] Alert system for anomalies
- [ ] REST API documentation
- [ ] Docker containerization
- [ ] Kubernetes deployment

---

**🎉 Happy Forecasting!** 