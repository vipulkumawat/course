#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Starting Network Traffic Analysis System"
echo "========================================="
echo "Working directory: $SCRIPT_DIR"

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11 not found. Using default python3..."
    PYTHON_CMD=python3
else
    PYTHON_CMD=python3.11
fi

# Create and activate virtual environment
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$SCRIPT_DIR/venv"
fi

source "$SCRIPT_DIR/venv/bin/activate"

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -q --upgrade pip
pip install -q -r "$SCRIPT_DIR/backend/requirements.txt"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
npm install --silent
cd "$SCRIPT_DIR"

# Run tests
echo ""
echo "Running tests..."
cd "$SCRIPT_DIR"
$PYTHON_CMD "$SCRIPT_DIR/tests/test_traffic_analysis.py"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo ""
    
    # Start backend
    echo "Starting backend server on http://localhost:8000..."
    cd "$SCRIPT_DIR"
    $PYTHON_CMD -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 3
    
    # Start frontend
    echo "Starting frontend on http://localhost:3000..."
    cd "$SCRIPT_DIR/frontend"
    npm run dev -- --host 0.0.0.0 &
    FRONTEND_PID=$!
    cd "$SCRIPT_DIR"
    
    echo ""
    echo "========================================="
    echo "✅ System started successfully!"
    echo "========================================="
    echo ""
    echo "🌐 Dashboard: http://localhost:3000"
    echo "🔌 API: http://localhost:8000"
    echo "📊 API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop..."
    echo ""
    
    # Save PIDs
    echo $BACKEND_PID > "$SCRIPT_DIR/.backend.pid"
    echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"
    
    # Wait for both processes
    wait $BACKEND_PID $FRONTEND_PID
else
    echo "❌ Tests failed. Please fix errors before starting."
    exit 1
fi
