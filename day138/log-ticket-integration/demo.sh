#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 JIRA/ServiceNow Ticket Integration Demo"
echo "========================================="

# Check if virtual environment exists
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    exit 1
fi

# Check if main module exists
if [ ! -f "$SCRIPT_DIR/src/main.py" ]; then
    echo "❌ Main application not found at $SCRIPT_DIR/src/main.py"
    exit 1
fi

# Check if Redis is running
if ! command -v redis-cli > /dev/null 2>&1 || ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis not running. Starting Redis with Docker..."
    if command -v docker > /dev/null 2>&1; then
        docker run -d --name redis-ticket-system -p 6379:6379 redis:7-alpine 2>/dev/null || docker start redis-ticket-system 2>/dev/null || true
        sleep 3
    else
        echo "❌ Docker not found. Please start Redis manually."
        exit 1
    fi
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Start system in background
echo "🚀 Starting system..."
cd "$SCRIPT_DIR"
python -m src.main &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for system to initialize..."
sleep 8

# Test system health
echo "🏥 Checking system health..."
if command -v curl > /dev/null 2>&1; then
    if command -v jq > /dev/null 2>&1; then
        curl -s http://localhost:8000/health | jq '.' || echo "Health check failed"
    else
        curl -s http://localhost:8000/health || echo "Health check failed"
    fi
else
    echo "⚠️  curl not found, skipping health check"
fi

# Generate test events
echo ""
echo "📊 Generating test events..."
if command -v curl > /dev/null 2>&1; then
    if command -v jq > /dev/null 2>&1; then
        curl -s -X POST "http://localhost:8000/api/events/test/generate?count=20" | jq '.' || echo "Event generation failed"
    else
        curl -s -X POST "http://localhost:8000/api/events/test/generate?count=20" || echo "Event generation failed"
    fi
else
    echo "⚠️  curl not found, skipping event generation"
fi

# Wait for processing
echo ""
echo "⏳ Waiting for event processing..."
sleep 10

# Check dashboard stats
echo ""
echo "📈 Dashboard Statistics:"
if command -v curl > /dev/null 2>&1; then
    if command -v jq > /dev/null 2>&1; then
        curl -s http://localhost:8000/api/dashboard/stats | jq '.' || echo "Dashboard stats failed"
    else
        curl -s http://localhost:8000/api/dashboard/stats || echo "Dashboard stats failed"
    fi
else
    echo "⚠️  curl not found, skipping dashboard stats"
fi

echo ""
echo "✅ Demo completed successfully!"
echo "🌐 Dashboard available at: http://localhost:8000"
echo "📊 API documentation at: http://localhost:8000/docs"

# Keep server running for manual testing
echo ""
echo "Press Ctrl+C to stop the demo server..."
wait $SERVER_PID
