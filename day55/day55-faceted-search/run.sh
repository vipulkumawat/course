#!/bin/bash
set -e

echo "🚀 Starting Faceted Search System..."

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "🔴 Starting Redis..."
    redis-server --daemonize yes
fi

# Start backend
echo "🐍 Starting Python backend..."
cd backend
python -m app.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend
echo "⚛️ Starting React frontend..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "✅ System started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"

# Wait for user input to stop
echo "Press Enter to stop all services..."
read

# Clean up
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
echo "🛑 Services stopped"
