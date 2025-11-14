#!/bin/bash

# Day 128: Multi-Language Logging Libraries - Stop Script

echo "🛑 Stopping Multi-Language Logging System..."

# Kill dashboard processes
pkill -f "dashboard/app.py" 2>/dev/null || true

# Kill demo processes
pkill -f "python_demo.py" 2>/dev/null || true
pkill -f "nodejs_demo.js" 2>/dev/null || true

# Stop Docker containers if running
if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null || true
fi

echo "✅ All processes stopped"
