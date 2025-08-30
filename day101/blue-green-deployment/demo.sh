#!/bin/bash

echo "🎬 Blue/Green Deployment Demo"
echo "============================="

# Check if system is running
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ System not running. Please run ./start.sh first"
    exit 1
fi

echo "📊 Current system status:"
curl -s http://localhost:8000/api/v1/status | python3 -m json.tool

echo ""
echo "🔄 Triggering deployment to version 2.1.0..."
curl -X POST http://localhost:8000/api/v1/deploy \
  -H "Content-Type: application/json" \
  -d '{"version": "v2.1.0", "config": {"new_feature": true}}' | python3 -m json.tool

echo ""
echo "⏳ Monitoring deployment progress..."
for i in {1..10}; do
    sleep 3
    echo "Status check $i:"
    curl -s http://localhost:8000/api/v1/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"  State: {data['state']} | Environment: {data['active_environment']} | Version: {data['version']}\")
"
    
    STATE=$(curl -s http://localhost:8000/api/v1/status | python3 -c "import sys, json; print(json.load(sys.stdin)['state'])")
    if [ "$STATE" = "completed" ] || [ "$STATE" = "failed" ]; then
        break
    fi
done

echo ""
echo "📈 Environment health status:"
curl -s http://localhost:8000/api/v1/environments | python3 -c "
import sys, json
data = json.load(sys.stdin)
for env, info in data.items():
    health = '✅ Healthy' if info['health']['is_healthy'] else '❌ Unhealthy'
    active = '🟢 Active' if info['active'] else '⚪ Standby'
    print(f'  {env.upper()}: {health} {active} (Port: {info[\"port\"]})')
"

echo ""
echo "📜 Recent deployment history:"
curl -s http://localhost:8000/api/v1/history | python3 -c "
import sys, json
data = json.load(sys.stdin)
deployments = data.get('deployments', [])
for dep in deployments[-3:]:  # Show last 3
    print(f\"  {dep['version']} - {dep['state']} ({dep['active_environment']}) - {dep['timestamp']}\")
"

echo ""
echo "🎉 Demo completed! Check the dashboard at http://localhost:3000"
