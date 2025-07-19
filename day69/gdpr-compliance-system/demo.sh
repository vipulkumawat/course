#!/bin/bash
set -e

echo "🎬 Starting GDPR Compliance System Demo..."

# Start the FastAPI backend server
echo "🚀 Starting FastAPI backend server..."
python3.13 -m uvicorn src.backend.api.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
sleep 5

# Test if server is running
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "✅ Server is running on http://localhost:8000"

# Create some sample data
echo "📊 Creating sample data..."
curl -X POST http://localhost:8000/api/user-data-tracking \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "data_type": "user_logs",
    "storage_location": "postgresql_main",
    "data_path": "/logs/user_activity"
  }'

echo ""

curl -X POST http://localhost:8000/api/user-data-tracking \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "data_type": "analytics_events",
    "storage_location": "elasticsearch_cluster",
    "data_path": "/analytics/user_events"
  }'

echo ""

# Create an erasure request
echo "🗑️ Creating erasure request..."
ERASURE_RESPONSE=$(curl -X POST http://localhost:8000/api/erasure-requests \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "request_type": "DELETE"
  }')

echo "Response: $ERASURE_RESPONSE"

# Get system statistics
echo "📈 Getting system statistics..."
curl -X GET http://localhost:8000/api/statistics

echo ""
echo "🎉 Demo completed!"
echo "📱 Access the web interface at: http://localhost:8000"
echo "📊 View system statistics at: http://localhost:8000/api/statistics"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"

# Keep the server running
wait $SERVER_PID
