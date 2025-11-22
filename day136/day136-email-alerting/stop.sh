#!/bin/bash
echo "🛑 Stopping Day 136: Email Alerting and Reporting System"

# Stop Docker Compose services
if command -v docker-compose &> /dev/null; then
    echo "🐳 Stopping Docker services..."
    docker-compose down
fi

# Stop local processes
echo "🐍 Stopping local processes..."
pkill -f "uvicorn src.main:app"
pkill -f "redis-server"

echo "✅ All services stopped!"
