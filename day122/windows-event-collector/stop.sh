#!/bin/bash

echo "🛑 Stopping Windows Event Log Agent System"
echo "=========================================="

# Stop Docker containers
echo "Stopping Docker containers..."
docker-compose down

# Stop native processes
echo "Stopping native processes..."
pkill -f "python src/main.py" || true

echo "✅ System stopped successfully!"
