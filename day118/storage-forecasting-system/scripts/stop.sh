#!/bin/bash

echo "🛑 Stopping Storage Forecasting System..."

# Kill backend if PID file exists
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
    echo "✅ Backend stopped"
fi

# Kill frontend if PID file exists
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
    echo "✅ Frontend stopped"
fi

# Kill any remaining processes
pkill -f "python -m src.main" 2>/dev/null
pkill -f "npm start" 2>/dev/null

echo "✅ System stopped successfully!"
