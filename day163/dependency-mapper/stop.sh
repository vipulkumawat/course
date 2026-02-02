#!/bin/bash

echo "Stopping Service Dependency Mapper..."

if [ -f .server.pid ]; then
    SERVER_PID=$(cat .server.pid)
    kill $SERVER_PID 2>/dev/null
    rm .server.pid
fi

if [ -f .http.pid ]; then
    HTTP_PID=$(cat .http.pid)
    kill $HTTP_PID 2>/dev/null
    rm .http.pid
fi

# Kill any remaining Python processes
pkill -f "backend/server.py" 2>/dev/null
pkill -f "http.server 8000" 2>/dev/null

echo "All services stopped."
