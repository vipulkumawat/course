#!/bin/bash

echo "🛑 Stopping Day 98: User Preferences System"

# Stop background processes
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
fi

if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
fi

# Stop Docker services
cd docker
docker-compose down

echo "✅ All services stopped!"
