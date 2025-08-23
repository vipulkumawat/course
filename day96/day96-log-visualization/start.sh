#!/bin/bash
set -e

echo "🚀 Starting Day 96: Data Visualization Components"
echo "================================================"

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Generate demo data
echo "📊 Generating demo data..."
cd scripts
python generate_demo_data.py
cd ..

# Start backend
echo "🌐 Starting backend server..."
cd backend
source ../venv/bin/activate
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start frontend
echo "⚛️ Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Services started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Store PIDs for cleanup
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

# Keep script running
wait
