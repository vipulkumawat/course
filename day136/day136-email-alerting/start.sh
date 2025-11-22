#!/bin/bash
echo "🚀 Starting Day 136: Email Alerting and Reporting System"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if Docker Compose is available
if command -v docker-compose &> /dev/null; then
    echo "🐳 Starting with Docker Compose..."
    docker-compose up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo "🔍 Checking service health..."
    docker-compose ps
    
    echo "✅ Services started successfully!"
    echo "📧 Dashboard: http://localhost:8000"
    echo "📊 Redis: localhost:6379"
else
    echo "🐍 Starting with local Python..."
    
    # Start Redis if not running
    if ! pgrep -x redis-server > /dev/null; then
        echo "🔄 Starting Redis..."
        redis-server --daemonize yes --port 6379
    fi
    
    # Activate virtual environment
    source venv/bin/activate || { echo "❌ Failed to activate virtual environment"; exit 1; }
    
    # Set environment variables
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
    export REDIS_URL="redis://localhost:6379/0"
    
    # Start the application
    echo "🚀 Starting FastAPI application..."
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
    
    echo "✅ Application started!"
    echo "📧 Dashboard: http://localhost:8000"
fi
