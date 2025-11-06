#!/bin/bash
# Start Dashboard Server
# Usage: ./start_dashboard.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dashboard script exists
DASHBOARD_SCRIPT="$SCRIPT_DIR/web/dashboard.py"
if [ ! -f "$DASHBOARD_SCRIPT" ]; then
    echo "❌ Dashboard script not found at $DASHBOARD_SCRIPT"
    exit 1
fi

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8000 is already in use. Checking if it's the dashboard..."
    PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Process $PID is using port 8000"
        read -p "   Kill existing process? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill $PID
            sleep 2
        else
            echo "❌ Exiting. Please free port 8000 or use a different port."
            exit 1
        fi
    fi
fi

echo "🚀 Starting GCP Log Integration Dashboard..."
echo "   Dashboard will be available at: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

cd "$SCRIPT_DIR"
uvicorn web.dashboard:app --host 0.0.0.0 --port 8000 --reload

