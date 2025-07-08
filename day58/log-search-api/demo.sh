#!/bin/bash

echo "🚀 Starting Log Search API Demo"
echo "================================"

# Kill processes using required ports
echo "🔍 Checking for processes using required ports..."

# Check and kill process on port 3000 (frontend)
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "⚠️  Found process using port 3000, killing it..."
    lsof -ti:3000 | xargs kill -9
    sleep 2
fi

# Check and kill process on port 8000 (backend)
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Found process using poyert 8000, killing it..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

echo "✅ Ports cleared successfully"

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Start services with Docker
echo "🐳 Starting services with Docker..."
docker-compose up -d elasticsearch redis

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Start backend
echo "🔧 Starting backend API..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "🎨 Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Demo setup complete!"
echo ""
echo "🔗 Access points:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/api/docs"
echo "   Health: http://localhost:8000/api/v1/health/"
echo ""
echo "📝 Demo credentials:"
echo "   Username: testuser"
echo "   Password: secret"
echo ""
echo "🛑 To stop demo: ./cleanup.sh"

# Save PIDs for cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid
