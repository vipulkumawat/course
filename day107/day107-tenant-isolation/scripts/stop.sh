#!/bin/bash

echo "🛑 Stopping Day 107: Tenant Isolation System"
echo "============================================="

# Stop services
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null || true
    rm .backend.pid
fi

if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null || true
    rm .frontend.pid
fi

# Kill any remaining processes
pkill -f "python src/api/main.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

echo "✅ All services stopped"
