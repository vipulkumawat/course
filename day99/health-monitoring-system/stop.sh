#!/bin/bash

echo "🛑 Stopping Health Monitoring System..."

# Kill processes if PID files exist
if [ -f mock.pid ]; then
    kill $(cat mock.pid) 2>/dev/null || true
    rm mock.pid
fi

if [ -f api.pid ]; then
    kill $(cat api.pid) 2>/dev/null || true
    rm api.pid
fi

# Kill any remaining processes
pkill -f "mock_services.py" 2>/dev/null || true
pkill -f "src.api.main" 2>/dev/null || true

echo "✅ All services stopped"
