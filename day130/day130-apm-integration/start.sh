#!/bin/bash

echo "🚀 Starting APM Integration System"
echo "================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./build.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Redis is already running
if pgrep -x redis-server > /dev/null || docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^.*redis.*$"; then
    echo "✅ Redis server is already running"
else
    echo "📡 Starting Redis server..."
    if command -v redis-server > /dev/null; then
        redis-server --daemonize yes --port 6379
        sleep 1
    elif command -v docker-compose > /dev/null || (command -v docker > /dev/null && docker compose version > /dev/null 2>&1); then
        echo "🐳 Starting Redis using Docker Compose..."
        if command -v docker-compose > /dev/null; then
            docker-compose up -d redis
        else
            docker compose up -d redis
        fi
        sleep 2
        echo "✅ Redis started via Docker"
    else
        echo "❌ Redis server not found and Docker is not available."
        echo "   Please install Redis or Docker to continue."
        exit 1
    fi
fi

# Check for duplicate backend processes
if pgrep -f "python.*api.server" > /dev/null; then
    echo "⚠️  Backend API is already running. Stopping existing instance..."
    pkill -f "python.*api.server"
    sleep 2
fi

# Start backend API
echo "🔧 Starting FastAPI backend..."
cd "$SCRIPT_DIR/src" || exit 1
python -m api.server &
BACKEND_PID=$!
cd "$SCRIPT_DIR" || exit 1

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

# Check for duplicate frontend processes
if pgrep -f "react-scripts start" > /dev/null || pgrep -f "npm.*start" > /dev/null; then
    echo "⚠️  Frontend is already running. Stopping existing instance..."
    pkill -f "react-scripts start"
    pkill -f "npm.*start"
    sleep 2
fi

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed. Please run ./build.sh first."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🌐 Starting React frontend..."
cd "$SCRIPT_DIR/frontend" || exit 1
npm start > /dev/null 2>&1 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR" || exit 1

echo ""
echo "✅ System started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Create PID file for cleanup
echo "$BACKEND_PID $FRONTEND_PID" > .pids

# Wait for interrupt
trap 'kill $(cat .pids) 2>/dev/null; rm -f .pids; exit' INT
wait
