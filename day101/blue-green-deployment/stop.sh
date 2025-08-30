#!/bin/bash

echo "🛑 Stopping Blue/Green Deployment System"
echo "======================================="

# Stop frontend if running
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "🌐 Stopping frontend dashboard..."
        kill $FRONTEND_PID
    fi
    rm -f .frontend.pid
fi

# Stop Docker services
echo "🐳 Stopping Docker services..."
docker-compose down

# Stop any remaining containers
echo "🧹 Cleaning up containers..."
docker stop $(docker ps -q --filter "name=blue-green") 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=blue-green") 2>/dev/null || true

# Clean up networks
docker network prune -f

echo "✅ Blue/Green Deployment System stopped successfully!"
