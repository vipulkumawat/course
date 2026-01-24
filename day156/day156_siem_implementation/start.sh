#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Day 156 SIEM System..."

# Check for duplicate services
echo "🔍 Checking for existing services..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Checking if it's our service..."
    EXISTING_PID=$(lsof -ti:8000)
    if [ -f ".api.pid" ] && [ "$(cat .api.pid)" == "$EXISTING_PID" ]; then
        echo "✅ Service already running with PID $EXISTING_PID"
        exit 0
    else
        echo "❌ Port 8000 is in use by another process (PID: $EXISTING_PID)"
        echo "   Please stop it first or use ./stop.sh"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start Redis (if not running)
echo "🔴 Checking Redis..."
REDIS_RUNNING=false

# Try to ping Redis
if command -v redis-cli > /dev/null 2>&1; then
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis is already running"
        REDIS_RUNNING=true
    elif command -v redis-server > /dev/null 2>&1; then
        echo "Starting Redis server..."
        redis-server --daemonize yes
        sleep 3
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis started successfully"
            REDIS_RUNNING=true
        fi
    fi
fi

# Try Docker Redis if local Redis not available
if [ "$REDIS_RUNNING" = false ]; then
    if command -v docker > /dev/null 2>&1; then
        echo "🐳 Trying to start Redis via Docker..."
        if ! docker ps | grep -q redis; then
            docker run -d --name siem-redis -p 6379:6379 redis:7-alpine > /dev/null 2>&1
            sleep 3
        fi
        if docker exec siem-redis redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis running in Docker"
            REDIS_RUNNING=true
        fi
    fi
fi

if [ "$REDIS_RUNNING" = false ]; then
    echo "⚠️  Warning: Redis is not available. Server may fail to start."
    echo "   Install Redis or use Docker: docker run -d -p 6379:6379 redis:7-alpine"
fi

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v || echo "⚠️  Some tests failed, but continuing..."

# Start API server in background
echo "🌐 Starting SIEM API server..."
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Wait for server to start
sleep 5

echo ""
echo "======================================================================"
echo "✅ SIEM System is running!"
echo "======================================================================"
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "🔌 API: http://localhost:8000"
echo "📈 Health: http://localhost:8000/health"
echo ""
echo "To generate test events, run:"
echo "  python scripts/generate_test_data.py"
echo ""
echo "To stop, run:"
echo "  ./stop.sh"
echo "======================================================================"

# Save PID
echo $API_PID > .api.pid
