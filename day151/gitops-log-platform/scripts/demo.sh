#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🎬 GitOps Workflow Demonstration"
echo "================================"

# Check if virtual environment exists (optional)
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Check if dashboard is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Dashboard is not running. Please start it with ./start.sh"
    exit 1
fi

echo ""
echo "1️⃣  Checking Dashboard Health..."
sleep 2
curl -s http://localhost:8000/health | $PYTHON_CMD -m json.tool || echo "Failed to get health"

echo ""
echo "2️⃣  Getting GitOps Status (before sync)..."
sleep 2
curl -s http://localhost:8000/api/status | $PYTHON_CMD -m json.tool || echo "Failed to get status"

echo ""
echo "3️⃣  Viewing Deployment History (before sync)..."
sleep 2
curl -s http://localhost:8000/api/deployments | $PYTHON_CMD -m json.tool || echo "Failed to get deployments"

echo ""
echo "4️⃣  Triggering Manual Sync (this will update metrics)..."
sleep 2
curl -s -X POST http://localhost:8000/api/sync | $PYTHON_CMD -m json.tool || echo "Failed to trigger sync"

echo ""
echo "5️⃣  Waiting for metrics to update..."
sleep 3

echo ""
echo "6️⃣  Getting Updated GitOps Status (after sync)..."
sleep 2
curl -s http://localhost:8000/api/status | $PYTHON_CMD -m json.tool || echo "Failed to get status"

echo ""
echo "7️⃣  Viewing Updated Deployment History..."
sleep 2
curl -s http://localhost:8000/api/deployments | $PYTHON_CMD -m json.tool || echo "Failed to get deployments"

echo ""
echo "8️⃣  Triggering another sync to show metrics incrementing..."
sleep 2
curl -s -X POST http://localhost:8000/api/sync | $PYTHON_CMD -m json.tool || echo "Failed to trigger sync"

sleep 2
echo ""
echo "9️⃣  Final Status Check..."
curl -s http://localhost:8000/api/status | $PYTHON_CMD -m json.tool || echo "Failed to get status"

echo ""
echo "✅ Demo Complete!"
echo ""
echo "📊 View full dashboard at: http://localhost:8000"
echo "📈 Metrics should now show non-zero values!"
