#!/bin/bash

echo "🛑 Stopping IOC Scanner System..."

# Kill Python processes
pkill -f "python -m src.main"
pkill -f "uvicorn"

# Kill Node processes
pkill -f "react-scripts"
pkill -f "node"

# Stop Redis
redis-cli shutdown 2>/dev/null || true

echo "✅ All services stopped"
