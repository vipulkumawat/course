#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting IOC Scanner System"
echo "=================================================="

# Check for duplicate services
echo "🔍 Checking for existing services..."

# Check Redis
if pgrep -f "redis-server" > /dev/null; then
    echo "⚠️  Redis is already running"
else
    echo "Starting Redis..."
    redis-server --daemonize yes --port 6379 || {
        echo "❌ Failed to start Redis"
        exit 1
    }
    sleep 2
fi

# Check API server
if pgrep -f "python.*src.main" > /dev/null || pgrep -f "uvicorn" > /dev/null; then
    echo "⚠️  API server is already running (PID: $(pgrep -f 'python.*src.main' || pgrep -f 'uvicorn'))"
    echo "   Stopping existing instance..."
    pkill -f "python.*src.main" || pkill -f "uvicorn"
    sleep 2
fi

# Check React dashboard
if pgrep -f "react-scripts" > /dev/null; then
    echo "⚠️  React dashboard is already running (PID: $(pgrep -f 'react-scripts'))"
    echo "   Stopping existing instance..."
    pkill -f "react-scripts"
    sleep 2
fi

# Verify we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Detect Python command
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python 3 not found. Please install Python 3.11 or later."
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv || {
        echo "❌ Failed to create virtual environment"
        exit 1
    }
fi

# Activate virtual environment
source venv/bin/activate || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}

# Start API server
echo "Starting API server..."
python -m src.main > api.log 2>&1 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✓ API server is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API server failed to start"
        kill $API_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Install React dependencies
cd web || {
    echo "❌ Failed to change to web directory"
    exit 1
}

if [ ! -d "node_modules" ]; then
    echo "Installing React dependencies..."
    npm install --silent || {
        echo "❌ Failed to install React dependencies"
        cd ..
        exit 1
    }
fi

# Start React dashboard
echo "Starting React dashboard..."
npm start > ../dashboard.log 2>&1 &
DASHBOARD_PID=$!

cd ..

echo ""
echo "✅ System started successfully!"
echo "API: http://localhost:8000"
echo "Dashboard: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping services...'; kill $API_PID $DASHBOARD_PID 2>/dev/null; pkill -f 'react-scripts' 2>/dev/null; redis-cli shutdown 2>/dev/null; echo '✅ All services stopped'; exit" INT TERM
wait
