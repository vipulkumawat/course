#!/bin/bash

echo "🛑 Stopping Tiered Storage System"
echo "=================================="

# Kill processes using PID files
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "✓ Backend stopped"
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "✓ Frontend stopped"
    rm frontend.pid
fi

# Kill by process name as backup
pkill -f "python -m src.main" 2>/dev/null
pkill -f "npm run dev" 2>/dev/null

echo "✅ All services stopped"
