#!/bin/bash

echo "🚀 Starting GDPR Compliance System..."

# Check if server is already running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "⚠️  Server is already running on http://localhost:8000"
    echo "📚 API documentation: http://localhost:8000/docs"
    echo "📊 Statistics: http://localhost:8000/api/statistics"
    exit 0
fi

# Start the FastAPI backend server
echo "🔧 Starting FastAPI backend server..."
python3.13 -m uvicorn src.backend.api.main:app --host 127.0.0.1 --port 8000 --reload &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
sleep 3

# Test if server is running
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Server started successfully!"
    echo "🌐 Web interface: http://localhost:8000"
    echo "📚 API documentation: http://localhost:8000/docs"
    echo "📊 Statistics: http://localhost:8000/api/statistics"
    echo ""
    echo "Press Ctrl+C to stop the server"
    
    # Keep the server running
    wait $SERVER_PID
else
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi 