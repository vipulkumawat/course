#!/bin/bash

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping BI Integration System..."

# Stop API server
if pgrep -f "uvicorn src.main:app" > /dev/null; then
    echo "Stopping API server..."
    pkill -f "uvicorn src.main:app" || true
    sleep 2
else
    echo "API server is not running"
fi

# Stop Docker services
if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        echo "Stopping Docker services..."
        docker-compose down
    else
        echo "Docker services are not running"
    fi
elif docker compose version &> /dev/null; then
    if docker compose ps | grep -q "Up"; then
        echo "Stopping Docker services..."
        docker compose down
    else
        echo "Docker services are not running"
    fi
else
    echo "⚠️  docker-compose not found, skipping Docker services"
fi

echo "✅ System stopped"
