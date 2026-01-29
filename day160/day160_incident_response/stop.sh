#!/bin/bash

echo "🛑 Stopping Incident Response System..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill all uvicorn processes related to this project
pkill -f "uvicorn src.api.main:app"

# Wait a moment for processes to stop
sleep 2

# Check if any processes are still running
if pgrep -f "uvicorn src.api.main:app" > /dev/null; then
    echo "⚠️  Some processes may still be running. Force killing..."
    pkill -9 -f "uvicorn src.api.main:app"
    sleep 1
fi

echo "✅ System stopped"
