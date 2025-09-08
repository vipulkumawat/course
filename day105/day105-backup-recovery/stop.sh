#!/bin/bash

echo "🛑 Stopping Day 105 services..."

# Stop Python processes
pkill -f "python src/main.py"
pkill -f "uvicorn"

# Stop Redis if we started it
if pgrep redis-server > /dev/null; then
    echo "🔴 Stopping Redis..."
    redis-cli shutdown
fi

echo "✅ All services stopped"
