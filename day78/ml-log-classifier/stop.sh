#!/bin/bash

echo "🛑 Stopping ML Log Classifier System"

# Kill API server if running
if [ -f ".api.pid" ]; then
    PID=$(cat .api.pid)
    if ps -p $PID > /dev/null; then
        echo "Stopping API server (PID: $PID)..."
        kill $PID
        rm .api.pid
    fi
fi

echo "✅ System stopped" 