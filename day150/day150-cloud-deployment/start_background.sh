#!/bin/bash
# Start Flask in background with proper logging

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/flask.log"
PID_FILE="$SCRIPT_DIR/flask.pid"

echo "🚀 Starting Flask Server in Background"
echo "======================================="

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./start.sh first."
    exit 1
fi

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Stop any existing Flask processes
echo "🛑 Stopping any existing Flask processes..."
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null || true
    rm -f "$PID_FILE"
fi
pkill -f "python.*web/app.py" 2>/dev/null || true
sleep 2

# Start Flask in background
echo "🌐 Starting Flask server..."
cd "$SCRIPT_DIR"
nohup "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/web/app.py" > "$LOG_FILE" 2>&1 &
WEB_PID=$!
echo $WEB_PID > "$PID_FILE"

# Wait a bit for server to start
sleep 3

# Check if it's still running
if kill -0 $WEB_PID 2>/dev/null; then
    echo "✅ Flask server started with PID: $WEB_PID"
    echo "📝 Logs: $LOG_FILE"
    echo "🛑 To stop: ./stop.sh or kill $WEB_PID"
    echo ""
    echo "🌐 Dashboard: http://localhost:5000"
    echo ""
    echo "View logs with: tail -f $LOG_FILE"
else
    echo "❌ Flask server failed to start. Check logs:"
    cat "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
