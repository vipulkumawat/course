#!/bin/bash

# Day 79: Log Clustering System - Stop Script

echo "🛑 Stopping Day 79: Log Clustering System"
echo "=========================================="

# Stop Docker services if running
if command -v docker-compose &> /dev/null; then
    echo "🔧 Stopping Docker services..."
    docker-compose down
fi

# Kill any remaining Python processes
pkill -f "python src/main.py" 2>/dev/null || true

echo "✅ System stopped successfully"
