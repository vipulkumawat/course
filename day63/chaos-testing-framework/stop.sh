#!/bin/bash

# Stop Chaos Testing Framework
echo "🛑 Stopping Chaos Testing Framework..."

# Stop backend
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🔄 Stopping backend..."
        kill $BACKEND_PID
        rm backend.pid
    fi
fi

# Stop frontend
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🔄 Stopping frontend..."
        kill $FRONTEND_PID
        rm frontend.pid
    fi
fi

# Stop any remaining processes on ports 3000 and 8000
echo "🔄 Stopping any remaining processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
pkill -f "python -m uvicorn src.web.main:app" > /dev/null 2>&1
pkill -f "npm start" > /dev/null 2>&1

# Stop Docker containers if Docker is available
if command -v docker > /dev/null 2>&1; then
    echo "🔄 Stopping Docker containers..."
    
    # Stop target services using docker-compose
    cd docker
    docker-compose down > /dev/null 2>&1
    cd ..
    
    # Stop and remove Redis container
    docker stop chaos-redis > /dev/null 2>&1
    docker rm chaos-redis > /dev/null 2>&1
    
    # Stop any remaining target containers
    docker stop log-collector-service message-queue-service log-processor-service > /dev/null 2>&1
    
    echo "✅ All Docker containers stopped"
fi

echo "✅ Chaos Testing Framework stopped"
