#!/bin/bash

echo "🚀 Starting Day 154: Disaster Recovery System"

# Get the script directory (full path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for duplicate services
echo "Checking for existing services..."
if pgrep -f "uvicorn src.api.main:app" > /dev/null; then
    echo "⚠️  Backend API is already running. Stopping existing instance..."
    pkill -f "uvicorn src.api.main:app"
    sleep 2
fi

if pgrep -f "react-scripts start" > /dev/null; then
    echo "⚠️  React dashboard is already running. Stopping existing instance..."
    pkill -f "react-scripts start"
    sleep 2
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source "$SCRIPT_DIR/venv/bin/activate"

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q

# Run tests
echo ""
echo "Running tests..."
python -m pytest "$SCRIPT_DIR/tests/" -v

# Start backend API
echo ""
echo "Starting backend API on port 8000..."
cd "$SCRIPT_DIR"
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Install and start React dashboard
echo ""
echo "Setting up React dashboard..."
cd "$SCRIPT_DIR/web"
if [ ! -d "node_modules" ]; then
    npm install
fi
npm start &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

# Wait a bit for everything to start
sleep 10

echo ""
echo "========================================"
echo "✅ DR System is running!"
echo "========================================"
echo ""
echo "📊 Dashboard: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Wait for user interrupt
wait
