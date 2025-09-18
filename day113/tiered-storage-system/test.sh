#!/bin/bash

set -e

echo "🧪 Testing Tiered Storage System"
echo "================================="

cd backend
source venv/bin/activate

# Run unit tests
echo "🔬 Running unit tests..."
python -m pytest tests/ -v --tb=short

echo ""
echo "🎯 Running integration tests..."

# Start backend for integration tests
python -m src.main &
BACKEND_PID=$!

# Wait for server to be ready
sleep 5

# Test API endpoints
echo "Testing API endpoints..."

# Health check
echo -n "Health check: "
if curl -s http://localhost:8000/api/health | grep -q "healthy"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test log storage
echo -n "Log storage: "
RESPONSE=$(curl -s -X POST http://localhost:8000/api/logs \
  -H "Content-Type: application/json" \
  -d '{"message":"Test log entry","level":"INFO","service":"test"}')

if echo $RESPONSE | grep -q "success"; then
    echo "✅ PASS"
    ENTRY_ID=$(echo $RESPONSE | grep -o '"entry_id":"[^"]*"' | cut -d'"' -f4)
else
    echo "❌ FAIL"
fi

# Test log retrieval
if [ ! -z "$ENTRY_ID" ]; then
    echo -n "Log retrieval: "
    if curl -s http://localhost:8000/api/logs/$ENTRY_ID | grep -q "Test log entry"; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
    fi
fi

# Test statistics
echo -n "Statistics API: "
if curl -s http://localhost:8000/api/stats | grep -q "tier_statistics"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Test migration
echo -n "Auto migration: "
if curl -s -X POST http://localhost:8000/api/auto-migrate | grep -q "success"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# Clean up
kill $BACKEND_PID 2>/dev/null

echo ""
echo "✅ All tests completed!"

cd ..
