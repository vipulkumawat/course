#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting Service Dependency Mapper..."
echo "Working directory: $SCRIPT_DIR"

# Create and activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with Python 3..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Start WebSocket server in background
echo "Starting WebSocket server..."
python "$SCRIPT_DIR/backend/server.py" "$SCRIPT_DIR/logs/sample.log" &
SERVER_PID=$!

# Start simple HTTP server for frontend
echo "Starting HTTP server for frontend..."
cd "$SCRIPT_DIR/frontend"
python -m http.server 8000 &
HTTP_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo "========================================="
echo "Service Dependency Mapper is running!"
echo "========================================="
echo "Dashboard: http://localhost:8000"
echo "WebSocket: ws://localhost:8765"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Save PIDs for cleanup
echo $SERVER_PID > .server.pid
echo $HTTP_PID > .http.pid

# Wait for interrupt
trap "kill $SERVER_PID $HTTP_PID 2>/dev/null; exit" INT TERM
wait
