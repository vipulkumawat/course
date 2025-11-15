#!/bin/bash

echo "🛑 Stopping APM Integration System"
echo "================================="

# Kill processes from PID file
if [ -f .pids ]; then
    kill $(cat .pids) 2>/dev/null
    rm -f .pids
    echo "✅ Backend and frontend stopped"
fi

# Stop any remaining processes
pkill -f "python.*api.server" 2>/dev/null
pkill -f "npm.*start" 2>/dev/null

# Stop Redis if we started it
redis-cli shutdown 2>/dev/null || true

# Stop Redis Docker container if it exists
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^.*redis.*$"; then
    if command -v docker-compose > /dev/null; then
        docker-compose stop redis 2>/dev/null || true
    else
        docker compose stop redis 2>/dev/null || true
    fi
    echo "✅ Redis Docker container stopped"
fi

echo "✅ All services stopped"
