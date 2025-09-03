#!/bin/bash

echo "🚀 Starting A/B Testing Framework..."

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start services with Docker
echo "🐳 Starting services with Docker..."
docker-compose up -d postgres redis

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Start backend
echo "🐍 Starting backend..."
cd backend
source ../venv/bin/activate
python src/main.py &
BACKEND_PID=$!
cd ..

# Start frontend
echo "⚛️ Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Services started!"
echo "📊 Backend API: http://localhost:8000"
echo "🌐 Frontend Dashboard: http://localhost:3000"
echo "📖 API Documentation: http://localhost:8000/docs"

# Save PIDs for stop script
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo "🎯 A/B Testing Framework is ready!"
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit' INT
wait
