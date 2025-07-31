#!/bin/bash
echo "🔧 Building, Testing, and Starting Day 80: Predictive Analytics System"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
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

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p {data,models/trained,logs}

# Run tests
echo "🧪 Running tests..."
export PYTHONPATH="$(pwd)"
python -m pytest tests/ -v

# Generate sample data
echo "📊 Generating sample data..."
export PYTHONPATH="$(pwd)"
python src/utils/data_generator.py

# Train models
echo "🤖 Training models..."
export PYTHONPATH="$(pwd)"
python src/models/model_trainer.py

# Test API endpoints
echo "🌐 Testing API..."
export PYTHONPATH="$(pwd)"
python -c "
from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get('/health')
print(f'Health check: {response.status_code}')
print(response.json())

response = client.get('/predictions')
print(f'Predictions: {response.status_code}')
"

echo "✅ Build and test completed successfully!"

# Install Node.js dependencies for frontend
echo "📦 Installing frontend dependencies..."
cd frontend && npm install && npm run build && cd ..

# Start Redis server (required for caching and background tasks)
echo "🔴 Starting Redis server..."
redis-server --daemonize yes --port 6379
sleep 2

# Start background services
echo "🔄 Starting background services..."
celery -A src.forecasting.tasks worker --loglevel=info --detach
celery -A src.forecasting.tasks beat --loglevel=info --detach

# Start the main API server
echo "🌐 Starting API server on http://localhost:8080"
export PYTHONPATH="$(pwd)"
python src/api/main.py &
API_PID=$!

# Start the dashboard
echo "🎯 Starting dashboard on http://localhost:3000"
cd frontend && npm start &
DASHBOARD_PID=$!

echo ""
echo "✅ System started successfully!"
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
echo "🛑 To stop the system, run: ./stop.sh"

# Keep track of PIDs for stop script
echo $API_PID > api.pid
echo $DASHBOARD_PID > dashboard.pid

echo "🎉 Build, test, and start process completed!" 