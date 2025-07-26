#!/bin/bash

echo "🛑 Stopping Delta Encoding Log System"

if [ -f .app.pid ]; then
    PID=$(cat .app.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Application stopped (PID: $PID)"
    else
        echo "ℹ️  Application not running"
    fi
    rm -f .app.pid
else
    echo "ℹ️  No PID file found"
fi

# Kill any remaining processes
pkill -f "src.main" 2>/dev/null || true

echo "🧹 Cleanup completed"
