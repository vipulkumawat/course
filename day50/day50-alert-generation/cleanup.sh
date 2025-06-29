#!/bin/bash

echo "🧹 Cleaning up Alert Generation System..."

# Kill any running Python processes
pkill -f "python src/main.py"

# Stop and remove Docker containers
docker-compose down -v

# Remove logs


echo "✅ Cleanup completed!"
