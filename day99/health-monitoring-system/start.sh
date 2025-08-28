#!/bin/bash

echo "🏥 Starting Health Monitoring System..."

# Activate virtual environment if not already active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    source venv/bin/activate
fi

# Start mock services in background with proper output redirection
echo "🔧 Starting mock services..."
nohup python src/utils/mock_services.py > mock_services.log 2>&1 &
MOCK_PID=$!

# Wait for mock services to start
sleep 5

# Start main application
echo "🚀 Starting health monitoring API..."
nohup python -m src.api.main > api.log 2>&1 &
API_PID=$!

# Wait for API to start
sleep 10

echo "✅ Health Monitoring System started!"
echo "📊 Dashboard: http://localhost:8000/dashboard"
echo "🔍 API Health: http://localhost:8000/health"
echo "📋 API Docs: http://localhost:8000/docs"

# Store PIDs for stop script
echo $MOCK_PID > mock.pid
echo $API_PID > api.pid

echo "💡 Use ./stop.sh to stop all services"
echo "🔄 Services will run in background..."
echo "📝 Check mock_services.log and api.log for service output"
