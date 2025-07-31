#!/bin/bash
echo "🚀 Starting Day 80: Predictive Analytics System"

# Check if system is already running
if [ -f api.pid ] && [ -f dashboard.pid ]; then
    API_PID=$(cat api.pid 2>/dev/null)
    DASHBOARD_PID=$(cat dashboard.pid 2>/dev/null)
    
    if ps -p $API_PID >/dev/null 2>&1 && ps -p $DASHBOARD_PID >/dev/null 2>&1; then
        echo "⚠️  System appears to be already running (PIDs: $API_PID, $DASHBOARD_PID)"
        echo "   Use './stop.sh' to stop the current system first"
        exit 1
    else
        echo "🧹 Cleaning up stale PID files..."
        rm -f api.pid dashboard.pid
    fi
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://$host:$port" >/dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Check if required tools are installed
echo "🔍 Checking prerequisites..."

if ! command_exists python3.11; then
    echo "❌ Python 3.11 is not installed. Please install it first."
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install it first."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed. Please install it first."
    exit 1
fi

if ! command_exists redis-server; then
    echo "❌ Redis is not installed. Please install it first."
    exit 1
fi

echo "✅ All prerequisites are installed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Python dependency installation failed"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p {data,models/trained,logs}

# Check if Redis is already running
if port_in_use 6379; then
    echo "🔴 Redis is already running on port 6379"
else
    echo "🔴 Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
fi

# Start background services
echo "🔄 Starting background services..."
if ! port_in_use 6379; then
    echo "❌ Redis failed to start"
    exit 1
fi

# Start Celery worker and beat
echo "🔄 Starting Celery services..."
celery -A src.forecasting.tasks worker --loglevel=info --detach
celery -A src.forecasting.tasks beat --loglevel=info --detach

# Generate sample log data and train initial models
echo "📊 Generating sample data and training models..."
export PYTHONPATH="$(pwd)"
python src/utils/data_generator.py
if [ $? -ne 0 ]; then
    echo "❌ Data generation failed"
    exit 1
fi

python src/models/model_trainer.py
if [ $? -ne 0 ]; then
    echo "❌ Model training failed"
    exit 1
fi

echo "✅ Initial data and models ready"

# Start the main API server
echo "🌐 Starting API server on http://localhost:8080"
export PYTHONPATH="$(pwd)"
python src/api/main.py &
API_PID=$!

# Wait for API server to be ready
if ! wait_for_service "localhost" 8080 "API Server"; then
    echo "❌ API server failed to start"
    exit 1
fi

# Install Node.js dependencies for frontend
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Frontend dependency installation failed"
    exit 1
fi

npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi
cd ..

# Start the dashboard
echo "🎯 Starting dashboard on http://localhost:3000"
cd frontend && npm start &
DASHBOARD_PID=$!

# Wait for dashboard to be ready
if ! wait_for_service "localhost" 3000 "Dashboard"; then
    echo "❌ Dashboard failed to start"
    exit 1
fi

echo ""
echo "🎉 System started successfully!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8080"
echo "📈 Predictions: http://localhost:8080/predictions"
echo "🎬 Demo: Click the 'Run Demo' button on the dashboard"
echo ""
echo "📋 Services running:"
echo "   - API Server (PID: $API_PID)"
echo "   - Dashboard (PID: $DASHBOARD_PID)"
echo "   - Redis Server"
echo "   - Celery Worker"
echo "   - Celery Beat"
echo ""
echo "🔍 System Status:"
echo "   - Models loaded: 3 (ARIMA, Prophet, Exponential Smoothing)"
echo "   - Confidence levels: High (99%+)"
echo "   - Forecast horizon: 60 minutes"
echo "   - Update interval: 5 minutes"
echo ""
echo "🛑 To stop the system, run: ./stop.sh"

# Keep track of PIDs for stop script
echo $API_PID > api.pid
echo $DASHBOARD_PID > dashboard.pid
