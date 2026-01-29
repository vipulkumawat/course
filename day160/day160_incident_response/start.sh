#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Day 160 Incident Response System"
echo "Working directory: $(pwd)"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the project directory."
    exit 1
fi

# Check for existing processes
if pgrep -f "uvicorn src.api.main:app" > /dev/null; then
    echo "⚠️  Warning: API server is already running. Stopping existing processes..."
    pkill -f "uvicorn src.api.main:app"
    sleep 2
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv || python3.11 -m venv venv || python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Run tests
echo "Running tests..."
python -m pytest tests/ -v --tb=short

if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi

echo "✅ Tests passed!"

# Start API server in background
echo "Starting API server..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Server is ready!"
        break
    fi
    sleep 1
done

# Check if server is running
if ! ps -p $API_PID > /dev/null; then
    echo "❌ Server failed to start!"
    exit 1
fi

echo ""
echo "🎯 System URLs:"
echo "   Dashboard: http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "💡 Test scenarios available in dashboard!"
echo ""
echo "Press Ctrl+C to stop..."

# Keep script running
wait $API_PID
