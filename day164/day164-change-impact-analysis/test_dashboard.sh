#!/bin/bash

echo "🧪 Testing Dashboard Metrics Update"
echo "===================================="

API_URL="http://localhost:8000"

# Test 1: Verify API is responding
echo ""
echo "Test 1: API Health Check"
echo "------------------------"
HEALTH=$(curl -s "$API_URL/health")
echo "$HEALTH" | python3 -m json.tool
if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
    exit 1
fi

# Test 2: Verify services endpoint
echo ""
echo "Test 2: Services Endpoint"
echo "-------------------------"
SERVICES=$(curl -s "$API_URL/services")
SERVICE_COUNT=$(echo "$SERVICES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['total'])")
echo "Total services: $SERVICE_COUNT"
if [ "$SERVICE_COUNT" -gt "0" ]; then
    echo "✅ Services endpoint working"
else
    echo "❌ No services found"
    exit 1
fi

# Test 3: Test analysis with non-zero metrics
echo ""
echo "Test 3: Analysis with Metrics"
echo "-----------------------------"
ANALYSIS=$(curl -s -X POST "$API_URL/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "infrastructure",
    "target_service": "rabbitmq-cluster",
    "change_description": "Dashboard metrics validation test"
  }')

RISK_SCORE=$(echo "$ANALYSIS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['risk_score'])")
BLAST_RADIUS=$(echo "$ANALYSIS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['blast_radius'])")
CRITICAL_PATH=$(echo "$ANALYSIS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['critical_path'])")

echo "Risk Score: $RISK_SCORE"
echo "Blast Radius: $BLAST_RADIUS"
echo "Critical Path: $CRITICAL_PATH"

if [ "$(echo "$RISK_SCORE > 0" | bc)" -eq 1 ] && [ "$BLAST_RADIUS" -gt 0 ]; then
    echo "✅ All metrics are non-zero"
    echo ""
    echo "Dashboard should display:"
    echo "  - Risk Score: $RISK_SCORE (with appropriate badge)"
    echo "  - Blast Radius: $BLAST_RADIUS services"
    echo "  - Critical Path: $CRITICAL_PATH"
    echo ""
    echo "✅ Dashboard metrics validation passed!"
else
    echo "❌ Metrics validation failed - some metrics are zero"
    exit 1
fi
