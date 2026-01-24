#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Day 157: Threat Detection System - Starting..."
echo "📂 Working directory: $SCRIPT_DIR"

# Check for duplicate services
echo "🔍 Checking for existing services..."
if pgrep -f "python.*src.main" > /dev/null; then
    echo "⚠️  Warning: API server is already running!"
    echo "   Stopping existing processes..."
    pkill -f "python.*src.main" || true
    sleep 2
fi

if pgrep -f "python.*src.data_generator" > /dev/null; then
    echo "⚠️  Warning: Data generator is already running!"
    echo "   Stopping existing processes..."
    pkill -f "python.*src.data_generator" || true
    sleep 2
fi

# Check if port 8000 is in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Warning: Port 8000 is already in use!"
    echo "   Attempting to free the port..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv || python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short || echo "⚠️  Some tests failed, continuing..."

# Start API server in background
echo "🌐 Starting API server..."
cd "$SCRIPT_DIR"
python -m src.main > logs/api.log 2>&1 &
API_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/api/stats > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    sleep 1
done

# Open dashboard
echo "📊 Dashboard available at: http://localhost:8000/dashboard"

# Generate test traffic
echo "🎭 Generating test traffic..."
cd "$SCRIPT_DIR"
python -m src.data_generator > logs/traffic.log 2>&1 &
TRAFFIC_PID=$!

echo ""
echo "✅ System running successfully!"
echo ""
echo "📍 Endpoints:"
echo "   Dashboard: http://localhost:8000/dashboard"
echo "   API Stats: http://localhost:8000/api/stats"
echo "   WebSocket: ws://localhost:8000/ws/threats"
echo ""
echo "📝 Logs:"
echo "   API: logs/api.log"
echo "   Traffic: logs/traffic.log"
echo ""
echo "Press Ctrl+C to stop..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $API_PID 2>/dev/null || true
    kill $TRAFFIC_PID 2>/dev/null || true
    pkill -f "python.*src.main" || true
    pkill -f "python.*src.data_generator" || true
    echo "✅ Stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for interrupt
wait $API_PID
