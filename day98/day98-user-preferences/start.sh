#!/bin/bash

echo "🚀 Starting Day 98: User Preferences System"

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Using python3..."
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python3.11"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start Redis with Docker Compose (PostgreSQL replaced with SQLite)
echo "🐳 Starting Redis with Docker..."
cd docker
docker-compose up -d redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Run database migrations (create tables) - using SQLite
echo "🗄️ Setting up database..."
cd ../backend
python -c "from src.database.connection import create_tables; create_tables()"
cd ..

# Start backend
echo "🚀 Starting backend server..."
cd backend
python -m src.main &
BACKEND_PID=$!
cd ..

# Start frontend
echo "⚛️ Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Save PIDs for cleanup
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo "✅ All services started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"

echo "Press any key to stop services..."
read -n 1

# Stop services
./stop.sh
