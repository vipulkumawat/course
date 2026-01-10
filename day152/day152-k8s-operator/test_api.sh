#!/bin/bash
# Simple test script for API server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Testing API server..."

# Start API server in background
python3 src/api/server.py > api_test.log 2>&1 &
API_PID=$!
echo "API server started with PID: $API_PID"

# Wait for server to start
sleep 3

# Test endpoints
echo ""
echo "Testing /api/stats endpoint..."
curl -s http://localhost:8000/api/stats | python3 -m json.tool || echo "Failed to get stats"

echo ""
echo "Testing /api/processors endpoint..."
curl -s http://localhost:8000/api/processors | python3 -m json.tool || echo "Failed to get processors"

echo ""
echo "Testing root endpoint..."
curl -s http://localhost:8000/ | python3 -m json.tool || echo "Failed to get root"

# Stop server
kill $API_PID 2>/dev/null
wait $API_PID 2>/dev/null

echo ""
echo "✅ API test complete"
