#!/bin/bash
set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting BI Integration System..."

# Check if already running
if pgrep -f "uvicorn src.main:app" > /dev/null; then
    echo "⚠️  API server is already running!"
    echo "Stopping existing instance..."
    pkill -f "uvicorn src.main:app" || true
    sleep 2
fi

# Check for duplicate docker services
if docker-compose ps | grep -q "Up"; then
    echo "⚠️  Docker services are already running"
    read -p "Do you want to restart them? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down
    fi
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found! Please run setup.sh first."
    exit 1
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose not found! Please install Docker Compose."
    exit 1
fi

# Start Docker services
echo "Starting infrastructure..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d influxdb redis timescaledb
else
    docker compose up -d influxdb redis timescaledb
fi

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found in virtual environment!"
    exit 1
fi

# Start API server
echo "Starting API server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait a moment and check if server started
sleep 3
if ! kill -0 $API_PID 2>/dev/null; then
    echo "❌ API server failed to start!"
    exit 1
fi

echo "✅ System started successfully!"
echo "📊 Dashboard: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "API PID: $API_PID"
echo ""
echo "Press Ctrl+C to stop"

# Wait for interrupt
wait $API_PID
