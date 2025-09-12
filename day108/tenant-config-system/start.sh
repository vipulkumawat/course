#!/bin/bash

echo "🚀 Starting Tenant Configuration System"
echo "======================================"

# Start Redis
echo "🔴 Starting Redis..."
redis-server --daemonize yes --port 6379

# Wait for Redis
sleep 2

# Start backend
echo "🔧 Starting backend..."
cd backend
source ../venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python src/main.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Start frontend development server
echo "⚛️ Starting frontend..."
cd ../frontend

# Try to install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install --silent --no-audit --no-fund
fi

# Start the frontend
if [ -d "node_modules" ] && [ -f "node_modules/.bin/react-scripts" ]; then
    echo "🚀 Starting React development server..."
    npm start &
    FRONTEND_PID=$!
else
    echo "⚠️  Frontend dependencies not found. Starting simple HTTP server..."
    python3 -m http.server 3000 --directory . &
    FRONTEND_PID=$!
fi

echo ""
echo "✅ System started successfully!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo '🛑 Stopping services...' && kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true && redis-cli shutdown" INT
wait
