#!/bin/bash

echo "🧹 Cleaning up Log Search API Demo"
echo "===================================="

# Kill backend process
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
    echo "✅ Backend stopped"
fi

# Kill frontend process
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
    echo "✅ Frontend stopped"
fi

# Stop Docker services
docker-compose down -v
echo "✅ Docker services stopped"

echo "🎉 Cleanup complete!"
