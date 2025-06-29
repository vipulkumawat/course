#!/bin/bash

echo "🚀 Day 50: Alert Generation System - Demo Script"
echo "================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
eval "$(pyenv init -)" && pip install -r requirements.txt

# Start infrastructure with Docker
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🗄️ Initializing database..."
eval "$(pyenv init -)" && python -c "
from config.database import init_database
if not init_database():
    exit(1)
"

# Run tests
echo "🧪 Running tests..."
eval "$(pyenv init -)" && python -m pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi

# Start the web interface (which includes the alert engine)
echo "🌐 Starting web interface with alert engine..."
eval "$(pyenv init -)" && PYTHONPATH=. python src/main.py web &
WEB_PID=$!

# Wait a moment for services to start
sleep 5

echo ""
echo "🎉 Alert Generation System is now running!"
echo "=========================================="
echo "📊 Web Dashboard: http://localhost:8000"
echo "🔍 API Endpoints:"
echo "   - GET  http://localhost:8000/stats"
echo "   - GET  http://localhost:8000/alerts"
echo "   - POST http://localhost:8000/test/inject_log"
echo ""
echo "Demo Instructions:"
echo "1. Open http://localhost:8000 in your browser"
echo "2. Click the test buttons to inject sample logs"
echo "3. Watch alerts appear in real-time"
echo "4. Test acknowledging and resolving alerts"
echo ""
echo "Press Ctrl+C to stop the demo"

# Keep the script running
trap "echo 'Stopping services...'; kill $WEB_PID 2>/dev/null; docker-compose down; exit" SIGINT

# Wait for user to stop
while true; do
    sleep 1
done
