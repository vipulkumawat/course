#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛑 Stopping Change Impact Analysis System..."

if [ -f "$SCRIPT_DIR/.api.pid" ]; then
    API_PID=$(cat "$SCRIPT_DIR/.api.pid")
    if kill $API_PID 2>/dev/null; then
        echo "✅ API server stopped (PID: $API_PID)"
    else
        echo "⚠️  API server process not found (PID: $API_PID)"
    fi
    rm "$SCRIPT_DIR/.api.pid"
fi

if [ -f "$SCRIPT_DIR/.web.pid" ]; then
    WEB_PID=$(cat "$SCRIPT_DIR/.web.pid")
    if kill $WEB_PID 2>/dev/null; then
        echo "✅ Web server stopped (PID: $WEB_PID)"
    else
        echo "⚠️  Web server process not found (PID: $WEB_PID)"
    fi
    rm "$SCRIPT_DIR/.web.pid"
fi

# Cleanup any remaining Python processes on ports
if lsof -ti:8000 > /dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    echo "✅ Cleaned up processes on port 8000"
fi

if lsof -ti:3000 > /dev/null 2>&1; then
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    echo "✅ Cleaned up processes on port 3000"
fi

echo "✅ All services stopped"
