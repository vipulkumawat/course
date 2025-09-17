#!/bin/bash

echo "🛑 Stopping SSO Log Platform..."

# Stop FastAPI application
pkill -f "uvicorn.*main:app"

# Stop Redis if running
if pgrep redis-server > /dev/null; then
    echo "📦 Stopping Redis server..."
    pkill redis-server
fi

echo "✅ All services stopped"
