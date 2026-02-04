#!/bin/bash
echo "🔍 Validating Dashboard and Metrics..."
echo "======================================"

# Wait for service to be ready
echo "⏳ Waiting for service to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        echo "✅ Service is responding"
        break
    fi
    sleep 1
done

# Test API endpoints
echo -e "\n📊 Testing SLO Status API:"
SLO_STATUS=$(curl -s http://localhost:8000/api/slo/status 2>&1)
if [ -z "$SLO_STATUS" ] || echo "$SLO_STATUS" | grep -q "Failed\|Error\|Connection"; then
    echo "❌ SLO Status API failed"
    echo "$SLO_STATUS"
    exit 1
else
    echo "✅ SLO Status API responding"
    echo "$SLO_STATUS" | python3 -m json.tool 2>/dev/null | head -30
    
    # Check for zero values
    if echo "$SLO_STATUS" | python3 -c "import sys, json; data=json.load(sys.stdin); zeros=[k for k,v in data.items() if v.get('current', 0) == 0]; exit(0 if not zeros else 1)" 2>/dev/null; then
        echo "✅ No zero values found in metrics"
    else
        echo "⚠️  Some metrics have zero values (may need more time to collect)"
    fi
fi

echo -e "\n🚨 Testing Violations API:"
VIOLATIONS=$(curl -s http://localhost:8000/api/violations 2>&1)
if [ -z "$VIOLATIONS" ] || echo "$VIOLATIONS" | grep -q "Failed\|Error\|Connection"; then
    echo "❌ Violations API failed"
    echo "$VIOLATIONS"
    exit 1
else
    echo "✅ Violations API responding"
    echo "$VIOLATIONS" | python3 -m json.tool 2>/dev/null
fi

echo -e "\n🌐 Testing Dashboard:"
DASHBOARD=$(curl -s http://localhost:8000/dashboard 2>&1)
if echo "$DASHBOARD" | grep -q "SLA Monitoring Dashboard"; then
    echo "✅ Dashboard is accessible"
else
    echo "❌ Dashboard not found or incorrect"
    echo "$DASHBOARD" | head -10
    exit 1
fi

echo -e "\n✅ All validations passed!"
echo "📊 Dashboard URL: http://localhost:8000/dashboard"
echo "📊 API Status: http://localhost:8000/api/slo/status"
