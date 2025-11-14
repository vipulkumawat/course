#!/bin/bash
# Start script for structured logging helpers

echo "🚀 Starting Structured Logging Helpers System"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Start web dashboard in background
echo "🌐 Starting web dashboard..."
python src/web/dashboard.py &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 3

# Run demonstration
echo "🎬 Running demonstration..."
python src/main.py

echo ""
echo "🌐 Web Dashboard: http://localhost:8000"
echo "📊 Dashboard PID: $DASHBOARD_PID"
echo ""
echo "Use 'kill $DASHBOARD_PID' to stop the dashboard"
echo "Or run: ./stop.sh"
