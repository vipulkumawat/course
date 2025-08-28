#!/bin/bash

echo "🎭 Health Monitoring System Demo"
echo "================================"

# Start services
./start.sh

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Test API endpoints
echo "🔍 Testing API endpoints..."

echo "1. System Health:"
curl -s http://localhost:8000/health | python -m json.tool | head -20

echo -e "\n2. Component Registration:"
curl -s -X POST http://localhost:8000/components/register \
  -H "Content-Type: application/json" \
  -d '{"component_id":"demo-service","name":"Demo Service","health_endpoint":"http://localhost:8001/health"}' \
  | python -m json.tool

echo -e "\n3. Alert Status:"
curl -s http://localhost:8000/alerts | python -m json.tool

echo -e "\n4. System Metrics:"
curl -s http://localhost:8000/health/metrics | python -m json.tool | head -30

echo -e "\n✅ Demo completed successfully!"
echo "🌐 Open http://localhost:8000/dashboard to see the live dashboard"
echo "📊 Dashboard will show real-time health updates"
echo "🛑 Run ./stop.sh to stop all services"
