#!/bin/bash
# Stop script for capacity planning system

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛑 Stopping Capacity Planning System..."

# Stop by PID file
if [ -f "$SCRIPT_DIR/api.pid" ]; then
    API_PID=$(cat "$SCRIPT_DIR/api.pid")
    if ps -p $API_PID > /dev/null 2>&1; then
        kill $API_PID
        echo "✅ API server stopped (PID: $API_PID)"
    fi
    rm "$SCRIPT_DIR/api.pid"
fi

# Stop dashboard server
if [ -f "$SCRIPT_DIR/dashboard.pid" ]; then
    DASHBOARD_PID=$(cat "$SCRIPT_DIR/dashboard.pid")
    if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
        kill $DASHBOARD_PID
        echo "✅ Dashboard server stopped (PID: $DASHBOARD_PID)"
    fi
    rm "$SCRIPT_DIR/dashboard.pid"
fi

# Also check for any remaining http.server processes on port 3000
REMAINING_DASH=$(ps aux | grep 'http.server.*3000' | grep -v grep | awk '{print $2}')
if [ -n "$REMAINING_DASH" ]; then
    echo "Stopping remaining dashboard processes: $REMAINING_DASH"
    echo "$REMAINING_DASH" | xargs kill 2>/dev/null || true
fi

# Also check for any remaining forecast_api processes
REMAINING=$(ps aux | grep -E 'forecast_api|src.api.forecast_api' | grep -v grep | awk '{print $2}')
if [ -n "$REMAINING" ]; then
    echo "Stopping remaining processes: $REMAINING"
    echo "$REMAINING" | xargs kill 2>/dev/null || true
fi

# Check port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    PORT_PID=$(lsof -ti:8000)
    if ps -p $PORT_PID > /dev/null 2>&1; then
        echo "⚠️  Process $PORT_PID still using port 8000. Stopping..."
        kill $PORT_PID 2>/dev/null || true
    fi
fi

echo "✅ System stopped"
