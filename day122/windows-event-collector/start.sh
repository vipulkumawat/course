#!/bin/bash

echo "🚀 Starting Windows Event Log Agent System"
echo "==========================================="

# Start with virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "📊 Starting native Python application..."
    python src/main.py &
    NATIVE_PID=$!
    echo "Native app started with PID: $NATIVE_PID"
fi

# Also start Docker for demonstration
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

echo "✅ System started successfully!"
echo ""
echo "📊 Dashboard: http://localhost:8080"
echo "🔍 Mock Log Server: http://localhost:8081"
echo "📈 Metrics: http://localhost:9090"
echo ""
echo "To stop: ./stop.sh"
