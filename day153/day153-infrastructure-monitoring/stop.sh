#!/bin/bash

echo "🛑 Stopping Day 153 Infrastructure Monitoring System"
echo "===================================================="

# Stop Python processes
if [ -f .exporter.pid ]; then
    kill $(cat .exporter.pid) 2>/dev/null
    rm .exporter.pid
    echo "✅ Stopped exporter"
fi

if [ -f .correlation.pid ]; then
    kill $(cat .correlation.pid) 2>/dev/null
    rm .correlation.pid
    echo "✅ Stopped correlation engine"
fi

if [ -f .dashboard.pid ]; then
    kill $(cat .dashboard.pid) 2>/dev/null
    rm .dashboard.pid
    echo "✅ Stopped dashboard"
fi

# Stop Docker services
echo "🐳 Stopping Docker services..."
docker-compose down

echo ""
echo "✅ All services stopped"
