#!/bin/bash

set -e

echo "🚀 Starting Webhook Integration System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run './build.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the backend server
echo "🌐 Starting webhook backend server..."
cd backend

# Use port from environment variable or default to 8001 (8000 is often used by Kubernetes)
PORT=${WEBHOOK_PORT:-8001}

# Check if port is available, if not try next port
if command -v lsof >/dev/null 2>&1; then
    while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
        echo "⚠️  Port $PORT is in use, trying next port..."
        PORT=$((PORT + 1))
    done
elif command -v netstat >/dev/null 2>&1; then
    while netstat -tuln 2>/dev/null | grep -q ":$PORT "; do
        echo "⚠️  Port $PORT is in use, trying next port..."
        PORT=$((PORT + 1))
    done
fi

uvicorn src.api.main:app --host 0.0.0.0 --port $PORT &
BACKEND_PID=$!
cd ..

echo "✅ System started successfully!"
echo "📊 Dashboard: http://localhost:$PORT"
echo "📡 API: http://localhost:$PORT/api"
echo "🧪 Test receiver: http://localhost:8080 (if using Docker)"

# Wait for user input to stop
echo "Press Ctrl+C to stop the system..."
trap "kill $BACKEND_PID 2>/dev/null; exit 0" INT
wait
