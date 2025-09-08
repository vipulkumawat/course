#!/bin/bash

echo "🚀 Starting Day 105: Automated Backup and Recovery System"
echo "=========================================================="

# Ensure virtual environment is activated
source venv/bin/activate

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Check if Redis is available
if command -v redis-server &> /dev/null; then
    echo "🔴 Starting Redis server..."
    redis-server --daemonize yes --port 6379
    sleep 2
else
    echo "⚠️ Redis not found, using in-memory coordination"
fi

echo "📊 Starting backup dashboard..."
echo "   Dashboard URL: http://localhost:8105"
echo "   WebSocket URL: ws://localhost:8106/ws"
echo ""
echo "🔧 Available endpoints:"
echo "   GET  /              - Dashboard UI"
echo "   GET  /api/stats     - System statistics"  
echo "   GET  /api/backups   - List backups"
echo "   POST /api/backup/trigger - Trigger backup"
echo "   POST /api/recovery/restore - Restore backup"
echo ""

# Start the main application
python src/main.py dashboard
