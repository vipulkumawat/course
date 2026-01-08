#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting GitOps Workflow System"
echo "=================================="
echo "Working directory: $SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Are you in the project directory?"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    if ! python3 -m venv venv 2>/dev/null; then
        echo "⚠️  venv module not available, trying alternative..."
        # Try installing python3-venv if possible, or use --user install
        if command -v apt-get >/dev/null 2>&1; then
            echo "Installing python3-venv (may require sudo)..."
            sudo apt-get update -qq && sudo apt-get install -y python3.12-venv python3-venv 2>/dev/null || true
        fi
        python3 -m venv venv || {
            echo "⚠️  Could not create venv, will install packages in user space"
            USE_USER_INSTALL=true
        }
    fi
fi

# Activate virtual environment or use user install
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "🔌 Activating virtual environment..."
    source venv/bin/activate
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo "⚠️  Using system Python (no venv available)"
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
    export PIP_USER=yes
fi

# Install dependencies
echo "📥 Installing dependencies..."
$PIP_CMD install --upgrade pip 2>/dev/null || true
$PIP_CMD install -r requirements.txt 2>&1 | grep -v "WARNING: Running pip as the 'root' user" || true

# Run tests
echo "🧪 Running tests..."
$PYTHON_CMD -m pytest tests/ -v || echo "⚠️  Some tests may have failed, continuing..."

# Check if dashboard is already running
if pgrep -f "python.*src/dashboard/app.py" > /dev/null; then
    echo "⚠️  Dashboard appears to be already running. Stopping existing instance..."
    pkill -f "python.*src/dashboard/app.py" || true
    sleep 2
fi

# Start dashboard in background
echo "🌐 Starting GitOps Dashboard..."
cd "$SCRIPT_DIR"
$PYTHON_CMD src/dashboard/app.py &
DASHBOARD_PID=$!

# Wait a moment for dashboard to start
sleep 3

# Check if dashboard started successfully
if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
    echo "❌ Dashboard failed to start"
    exit 1
fi

echo ""
echo "✅ GitOps System Started!"
echo "=================================="
echo "📊 Dashboard: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🆔 Dashboard PID: $DASHBOARD_PID"
echo ""
echo "To stop: ./stop.sh or pkill -f 'python.*src/dashboard/app.py'"
echo ""

# Keep script running
wait $DASHBOARD_PID
