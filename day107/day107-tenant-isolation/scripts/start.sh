#!/bin/bash
set -e

echo "🚀 Starting Day 107: Tenant Isolation System"
echo "============================================="

# Start backend
echo "🔧 Starting backend server..."
cd backend
source ../venv/bin/activate
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python src/api/main.py &
BACKEND_PID=$!

cd ..

# Start frontend  
echo "⚛️ Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!

cd ..

echo "✅ System started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"

# Store PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for interrupt
trap 'kill $(cat .backend.pid .frontend.pid 2>/dev/null) 2>/dev/null; rm -f .backend.pid .frontend.pid; exit' INT
wait
