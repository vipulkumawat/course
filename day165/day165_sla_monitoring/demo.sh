#!/bin/bash
echo "📊 SLA Monitoring System - Demo"
echo "================================"
sleep 3

echo -e "\n1. API Health:"
curl -s http://localhost:8000/ | python3 -m json.tool

echo -e "\n\n2. SLO Status:"
curl -s http://localhost:8000/api/slo/status | python3 -m json.tool

echo -e "\n\n3. Active Violations:"
curl -s http://localhost:8000/api/violations | python3 -m json.tool

echo -e "\n\n✅ Demo complete!"
echo "Monitor console for real-time violations"
