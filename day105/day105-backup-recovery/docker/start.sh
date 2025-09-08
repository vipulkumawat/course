#!/bin/bash

# Start Redis server
redis-server --daemonize yes

# Wait for Redis to start
sleep 2

# Start the application
cd /app
export PYTHONPATH=/app/src:$PYTHONPATH
python src/main.py
