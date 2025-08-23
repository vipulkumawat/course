#!/bin/bash

echo "🛑 Stopping Day 96 services..."

# Kill backend if running
if [ -f backend.pid ]; then
    BACKEND_PID=$(cat backend.pid)
    kill $BACKEND_PID 2>/dev/null || echo "Backend already stopped"
    rm backend.pid
fi

# Kill frontend if running
if [ -f frontend.pid ]; then
    FRONTEND_PID=$(cat frontend.pid)
    kill $FRONTEND_PID 2>/dev/null || echo "Frontend already stopped"
    rm frontend.pid
fi

# Kill any remaining Node.js and Python processes
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "python -m src.main" 2>/dev/null || true

echo "✅ All services stopped"
