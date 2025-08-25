#!/bin/bash

echo "🚀 Starting Day 97: Saved Searches and Alerts System"
echo "============================================================"

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Check if installation was successful
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
"

# Check if database initialization was successful
if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize database"
    exit 1
fi

# Start backend server
echo "🔧 Starting backend server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ../frontend

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
npm install

# Check if npm install was successful
if [ $? -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

# Start frontend development server
echo "🎨 Starting frontend server..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ System started successfully!"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Process IDs saved to .pids file"
echo "Use ./stop.sh to stop all services"

# Save process IDs
echo "$BACKEND_PID" > ../.backend_pid
echo "$FRONTEND_PID" > ../.frontend_pid

wait
