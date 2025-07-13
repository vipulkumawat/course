#!/bin/bash

# Start Chaos Testing Framework
echo "🌪️ Starting Chaos Testing Framework..."

# Check if already running
if pgrep -f "python -m src.web.main" > /dev/null; then
    echo "❌ Backend already running"
    exit 1
fi

if pgrep -f "npm start" > /dev/null; then
    echo "❌ Frontend already running"
    exit 1
fi

# Start Docker containers if Docker is available
if command -v docker > /dev/null 2>&1; then
    echo "🔄 Starting Docker containers..."
    
    # Start Redis container
    docker run -d --name chaos-redis -p 6379:6379 redis:7.2-alpine > /dev/null 2>&1 || echo "Redis already running"
    
    # Start target services using docker-compose
    cd docker
    docker-compose up -d target-log-collector target-message-queue target-log-processor > /dev/null 2>&1
    cd ..
    
    # Verify containers are running
    echo "✅ Docker containers started:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(chaos-redis|log-collector-service|message-queue-service|log-processor-service)"
else
    echo "⚠️  Docker not available - chaos scenarios will not work"
fi

# Start backend
echo "🔄 Starting backend API..."
source venv/bin/activate
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m uvicorn src.web.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo $BACKEND_PID > backend.pid

# Start frontend
echo "🔄 Starting frontend..."
cd frontend
npm start > /dev/null 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend healthy: http://localhost:8000"
else
    echo "❌ Backend failed to start"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend healthy: http://localhost:3000"
else
    echo "❌ Frontend failed to start"
fi

echo ""
echo "🎯 Chaos Testing Framework is running!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API: http://localhost:8000"
echo ""
echo "🐳 Docker Services:"
echo "   - Redis: localhost:6379"
echo "   - Log Collector: localhost:8001"
echo "   - Message Queue: localhost:5672 (Management: localhost:15672)"
echo "   - Log Processor: localhost:8002"
echo ""
echo "Use ./stop.sh to stop all services"
