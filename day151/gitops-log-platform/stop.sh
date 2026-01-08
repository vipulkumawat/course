#!/bin/bash

echo "🛑 Stopping GitOps System..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill dashboard process
echo "Stopping dashboard..."
pkill -f "python.*src/dashboard/app.py" || pkill -f "python.*dashboard/app.py" || true

# Kill controller process
echo "Stopping controller..."
pkill -f "python.*src/main.py" || pkill -f "python.*main.py" || true

# Wait a moment
sleep 2

# Check if processes are still running
if pgrep -f "python.*src/dashboard/app.py" > /dev/null; then
    echo "⚠️  Dashboard still running, force killing..."
    pkill -9 -f "python.*src/dashboard/app.py" || true
fi

if pgrep -f "python.*src/main.py" > /dev/null; then
    echo "⚠️  Controller still running, force killing..."
    pkill -9 -f "python.*src/main.py" || true
fi

echo "✅ GitOps System stopped"
