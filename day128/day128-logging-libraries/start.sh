#!/bin/bash

# Day 128: Multi-Language Logging Libraries - Start Script
set -e

echo "🚀 Starting Multi-Language Logging System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Virtual environment not found. Running build script..."
    ./build.sh
fi

# Activate virtual environment
source venv/bin/activate

# Start dashboard
echo "🌐 Starting web dashboard..."

# Get WSL IP address for Windows host access
WSL_IP=$(hostname -I | awk '{print $1}')
echo "📊 Dashboard will be available at:"
echo "   ✅ http://127.0.0.1:5000 (RECOMMENDED - use this in your browser)"
echo "   ⚠️  http://localhost:5000 (may have IPv6 issues)"
if [ ! -z "$WSL_IP" ]; then
    echo "   🌐 http://${WSL_IP}:5000 (from Windows host if WSL2 port forwarding doesn't work)"
fi
echo "🔌 API endpoint: http://127.0.0.1:5000/api/logs"
echo ""
echo "Press Ctrl+C to stop the dashboard"

python dashboard/app.py
