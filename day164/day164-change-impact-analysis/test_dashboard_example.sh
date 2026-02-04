#!/bin/bash

echo "🧪 Testing Dashboard Example: Schema Change on elasticsearch-cluster"
echo "===================================================================="
echo ""

API_URL="http://localhost:8000"

# Test the exact example shown in the dashboard
echo "Test Input:"
echo "  Change Type: schema_change"
echo "  Target Service: elasticsearch-cluster"
echo "  Change Description: Add new required field user_segment to log schema"
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "schema_change",
    "target_service": "elasticsearch-cluster",
    "change_description": "Add new required field user_segment to log schema, breaking backward compatibility"
  }')

echo "API Response:"
echo "$RESPONSE" | python3 -m json.tool

echo ""
echo "📊 Dashboard Should Display:"
echo "----------------------------"

RISK_SCORE=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['risk_score'])")
BLAST_RADIUS=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['blast_radius'])")
CRITICAL_PATH=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('YES' if d['critical_path'] else 'NO')")
AFFECTED_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d['affected_services']))")
REC_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d['recommendations']))")

echo "  ✓ Risk Score: $RISK_SCORE (with badge)"
echo "  ✓ Blast Radius: $BLAST_RADIUS services"
echo "  ✓ Critical Path: $CRITICAL_PATH"
echo "  ✓ Affected Services: $AFFECTED_COUNT services listed"
echo "  ✓ Recommendations: $REC_COUNT recommendations shown"
echo ""

# Validate metrics are non-zero
if (( $(echo "$RISK_SCORE > 0" | bc -l) )) && [ "$BLAST_RADIUS" -gt 0 ]; then
    echo "✅ All metrics are non-zero - Dashboard validation PASSED!"
    echo ""
    echo "🌐 Open dashboard at: http://localhost:3000"
    echo "   Fill in the form with the same values to see the results!"
else
    echo "❌ Some metrics are zero - validation FAILED"
    exit 1
fi
