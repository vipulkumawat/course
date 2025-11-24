#!/bin/bash

echo "🛑 Stopping Webhook Integration System..."

# Kill Python processes
pkill -f "python.*main.py" 2>/dev/null || true

# Stop Docker containers
docker-compose down 2>/dev/null || true

echo "✅ System stopped successfully!"
