#!/bin/bash

echo "🛑 Stopping A/B Testing Framework..."

# Kill backend and frontend processes
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null || true
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null || true
    rm frontend.pid
fi

# Stop Docker services
docker-compose down

echo "✅ All services stopped"
