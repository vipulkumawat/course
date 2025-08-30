#!/bin/bash

echo "🚀 Starting Blue/Green Deployment System"
echo "========================================"

# Check if Python 3.11 is available
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "❌ Python 3.11+ required but not found"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create and activate virtual environment
echo "📦 Setting up virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📥 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Build Docker images
echo "🐳 Building Docker images..."
docker build -t log-processor:latest -f docker/Dockerfile.log-processor .
docker build -t deployment-controller:latest -f docker/Dockerfile.controller .

# Start services with Docker Compose
echo "🔧 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 20

# Test service health
echo "🏥 Testing service health..."
curl -f http://localhost:8000/health || echo "⚠️ Controller not ready yet"
curl -f http://localhost:8001/health || echo "⚠️ Blue environment not ready yet"
curl -f http://localhost:8002/health || echo "⚠️ Green environment not ready yet"

# Start frontend development server
echo "🌐 Starting frontend dashboard..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 10

echo ""
echo "✅ Blue/Green Deployment System Started Successfully!"
echo ""
echo "🌐 Access Points:"
echo "   • Deployment Controller API: http://localhost:8000"
echo "   • Blue Environment: http://localhost:8001"
echo "   • Green Environment: http://localhost:8002"
echo "   • Frontend Dashboard: http://localhost:3000"
echo "   • Load Balancer: http://localhost:80"
echo ""
echo "🔧 Management:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop system: ./stop.sh"
echo ""

# Store frontend PID for cleanup
echo $FRONTEND_PID > .frontend.pid

echo "📊 Running integration tests..."
sleep 5
$PYTHON_CMD backend/tests/integration_test.py

echo ""
echo "🎉 System is ready for blue/green deployments!"
echo "   Open http://localhost:3000 to access the dashboard"
