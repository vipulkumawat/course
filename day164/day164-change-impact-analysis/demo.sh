#!/bin/bash

echo "🎬 Running Change Impact Analysis Demo"
echo "======================================"

# Ensure API is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ API server not running. Start with ./start.sh first"
    exit 1
fi

echo ""
echo "Test 1: Low Risk Change (Configuration Update)"
echo "----------------------------------------------"
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "configuration",
    "target_service": "reporting-service",
    "change_description": "Update report refresh interval"
  }' | python -m json.tool

echo ""
echo ""
echo "Test 2: Medium Risk Change (API Modification)"
echo "---------------------------------------------"
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "api_modification",
    "target_service": "log-enrichment",
    "change_description": "Add new enrichment field"
  }' | python -m json.tool

echo ""
echo ""
echo "Test 3: High Risk Change (Infrastructure)"
echo "-----------------------------------------"
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_type": "infrastructure",
    "target_service": "rabbitmq-cluster",
    "change_description": "Upgrade RabbitMQ to new major version"
  }' | python -m json.tool

echo ""
echo ""
echo "✅ Demo completed!"
echo "🌐 View results in dashboard: http://localhost:3000"
