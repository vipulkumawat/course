#!/bin/bash

echo "🚀 Starting SSO Log Platform..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run build.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "📦 Starting Redis server..."
    redis-server --daemonize yes --appendonly yes
    sleep 2
fi

# Start the application
echo "🌐 Starting FastAPI application on http://localhost:8000"
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
