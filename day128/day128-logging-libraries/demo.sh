#!/bin/bash

# Day 128: Multi-Language Logging Libraries - Demo Script
set -e

echo "🎬 Starting Multi-Language Logging Demo..."

# Activate Python environment
source venv/bin/activate

# Start dashboard in background
echo "🌐 Starting web dashboard..."
python dashboard/app.py &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 5

# Check if dashboard is running
if ! curl -s http://localhost:5000 > /dev/null; then
    echo "❌ Dashboard failed to start"
    kill $DASHBOARD_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Dashboard running at http://localhost:5000"

# Run integration tests
echo "🧪 Running integration tests..."
python tests/test_integration.py

# Start demo clients in background
echo "🚀 Starting demo clients..."

# Python demo
python examples/python_demo.py &
PYTHON_PID=$!

# Node.js demo (if available)
if command -v node &> /dev/null; then
    cd nodejs-lib && node ../examples/nodejs_demo.js &
    NODEJS_PID=$!
    cd ..
fi

echo "📊 Demo clients running. Check dashboard at http://localhost:5000"
echo "⏳ Demo will run for 60 seconds..."

# Wait for demo duration
sleep 60

# Cleanup
echo "🧹 Cleaning up demo processes..."
kill $PYTHON_PID 2>/dev/null || true
kill $NODEJS_PID 2>/dev/null || true
kill $DASHBOARD_PID 2>/dev/null || true

echo "✅ Demo completed successfully!"
echo ""
echo "📋 Demo Summary:"
echo "   - Multi-language logging libraries demonstrated"
echo "   - Real-time dashboard showed log aggregation"
echo "   - Integration tests verified functionality"
echo "   - Production-ready client libraries created"
