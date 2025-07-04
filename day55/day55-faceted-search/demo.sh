#!/bin/bash
set -e

echo "🎬 Faceted Search System Demo"
echo "============================="

# Check if services are running
echo "🔍 Checking system health..."
curl -s http://localhost:8000/health | jq

echo -e "\n📊 Generating sample data..."
curl -s -X POST "http://localhost:8000/api/logs/generate?count=100" | jq

echo -e "\n⏳ Waiting for indexing..."
sleep 3

echo -e "\n🔍 Testing search API..."
curl -s -X POST "http://localhost:8000/api/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "", "filters": {}, "limit": 5}' | jq '.logs | length'

echo -e "\n📈 Getting facets..."
curl -s "http://localhost:8000/api/search/facets" | jq '.facets | length'

echo -e "\n🎯 Testing filtered search..."
curl -s -X POST "http://localhost:8000/api/search/" \
  -H "Content-Type: application/json" \
  -d '{"query": "", "filters": {"level": ["error"]}, "limit": 3}' | jq '.total_count'

echo -e "\n✅ Demo completed! Visit http://localhost:3000 to explore the UI"
