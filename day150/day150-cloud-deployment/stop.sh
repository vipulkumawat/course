#!/bin/bash
# Stop script for Day 150

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/flask.pid"

echo "🛑 Stopping Flask services..."

# Kill using PID file if it exists
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "   Stopping Flask (PID: $OLD_PID)..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$OLD_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
fi

# Kill Flask app processes by pattern
FLASK_PIDS=$(pgrep -f "python.*web/app.py" 2>/dev/null || true)
if [ -n "$FLASK_PIDS" ]; then
    echo "   Stopping Flask dashboard (PIDs: $FLASK_PIDS)..."
    pkill -f "python.*web/app.py" 2>/dev/null || true
    sleep 1
    # Force kill if still running
    pkill -9 -f "python.*web/app.py" 2>/dev/null || true
fi

# Also kill any flask run processes
pkill -f "flask run" 2>/dev/null || true

# Check for any remaining processes
REMAINING=$(pgrep -f "python.*web/app.py" 2>/dev/null || true)
if [ -z "$REMAINING" ]; then
    echo "✅ All Flask services stopped"
else
    echo "⚠️  Warning: Some processes may still be running: $REMAINING"
    echo "   You may need to kill them manually: kill $REMAINING"
fi
