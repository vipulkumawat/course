#!/bin/bash

echo "🛑 Stopping SIEM System..."

# Kill API server
if [ -f ".api.pid" ]; then
    kill $(cat .api.pid) 2>/dev/null
    rm .api.pid
fi

# Stop Redis
redis-cli shutdown 2>/dev/null

echo "✅ SIEM System stopped"
