#!/bin/bash
# Validate dashboard metrics are non-zero and updating

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Validating Dashboard Metrics"
echo "================================"

# Start API server
echo "Starting API server..."
python3 src/api/server.py > api_validate.log 2>&1 &
API_PID=$!
echo "API server PID: $API_PID"
sleep 3

# Test metrics
echo ""
echo "Testing /api/stats endpoint..."
STATS=$(curl -s http://localhost:8000/api/stats)
echo "$STATS" | python3 -m json.tool

TOTAL_PROC=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_processors'])")
TOTAL_REPL=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_replicas'])")
READY_REPL=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['ready_replicas'])")
ACTIVE_PROC=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['active_processors'])")

echo ""
echo "Metrics Summary:"
echo "  Total Processors: $TOTAL_PROC"
echo "  Active Processors: $ACTIVE_PROC"
echo "  Total Replicas: $TOTAL_REPL"
echo "  Ready Replicas: $READY_REPL"

# Validate metrics are non-zero
VALID=true
if [ "$TOTAL_PROC" -eq 0 ]; then
    echo "❌ ERROR: Total processors is zero!"
    VALID=false
fi

if [ "$TOTAL_REPL" -eq 0 ]; then
    echo "❌ ERROR: Total replicas is zero!"
    VALID=false
fi

if [ "$READY_REPL" -eq 0 ]; then
    echo "❌ ERROR: Ready replicas is zero!"
    VALID=false
fi

if [ "$VALID" = true ]; then
    echo ""
    echo "✅ All metrics are non-zero!"
else
    echo ""
    echo "❌ Some metrics are zero - validation failed!"
fi

# Test processors endpoint
echo ""
echo "Testing /api/processors endpoint..."
PROCESSORS=$(curl -s http://localhost:8000/api/processors)
PROC_COUNT=$(echo "$PROCESSORS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "Found $PROC_COUNT processors"

if [ "$PROC_COUNT" -gt 0 ]; then
    echo "$PROCESSORS" | python3 -m json.tool | head -20
    echo "✅ Processors endpoint working"
else
    echo "❌ No processors found"
    VALID=false
fi

# Test dashboard HTML
echo ""
echo "Testing dashboard HTML..."
DASHBOARD=$(curl -s http://localhost:8000/ | head -5)
if echo "$DASHBOARD" | grep -q "Log Platform Operator Dashboard"; then
    echo "✅ Dashboard HTML is accessible"
else
    echo "⚠️  Dashboard HTML may not be served correctly"
fi

# Cleanup
kill $API_PID 2>/dev/null
wait $API_PID 2>/dev/null

echo ""
if [ "$VALID" = true ]; then
    echo "✅ Dashboard validation PASSED"
    exit 0
else
    echo "❌ Dashboard validation FAILED"
    exit 1
fi
