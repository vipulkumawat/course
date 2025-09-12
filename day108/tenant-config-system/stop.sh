#!/bin/bash

echo "🛑 Stopping Tenant Configuration System"
echo "====================================="

# Kill processes
pkill -f "python src/main.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

# Stop Redis
redis-cli shutdown 2>/dev/null || true

echo "✅ All services stopped"
