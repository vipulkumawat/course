#!/bin/bash

# Day 79: Log Clustering System - Start Script

echo "🚀 Starting Day 79: Log Clustering for Pattern Discovery"
echo "========================================================"

# Activate virtual environment
source venv/bin/activate

# Start Redis (if using Docker)
if command -v docker-compose &> /dev/null; then
    echo "🔧 Starting Redis with Docker..."
    docker-compose up -d redis
    sleep 5
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis not available. Some features may not work."
fi

# Start the application
echo "🌐 Starting clustering web application..."
echo "Dashboard will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the application"
echo ""

python src/main.py
