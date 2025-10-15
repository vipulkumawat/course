#!/bin/bash

echo "🚀 Starting Storage Forecasting System..."

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PWD}/backend/src:$PYTHONPATH"

# Start backend in background
echo "🔧 Starting backend server..."
cd backend && python -m src.main &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 5

# Start frontend in background
echo "🌐 Starting frontend server..."
cd frontend && npm start &
FRONTEND_PID=$!
cd ..

echo "✅ System started successfully!"
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend Dashboard: http://localhost:3000"
echo "📖 API Docs: http://localhost:8000/docs"

# Save PIDs for stop script
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Wait for user input to stop
echo "Press Ctrl+C to stop the system..."
wait
