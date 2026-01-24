#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 Starting cleanup process..."

# Stop all Python services
echo "🛑 Stopping Python services..."
pkill -f "python.*src.main" 2>/dev/null || true
pkill -f "python.*src.data_generator" 2>/dev/null || true
sleep 2

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
if command -v docker-compose &> /dev/null; then
    docker-compose down 2>/dev/null || true
elif command -v docker &> /dev/null; then
    docker compose down 2>/dev/null || true
fi

# Remove Docker containers
echo "🗑️  Removing Docker containers..."
docker ps -aq --filter "name=threat-detection" | xargs -r docker rm -f 2>/dev/null || true

# Remove unused Docker resources
echo "🧹 Cleaning up unused Docker resources..."
docker container prune -f 2>/dev/null || true
docker image prune -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true
docker network prune -f 2>/dev/null || true

# Remove Docker images for this project
echo "🗑️  Removing Docker images..."
docker images | grep -E "threat-detection|day157" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# Remove all unused Docker resources (more aggressive)
echo "🧹 Removing all unused Docker resources..."
docker system prune -af --volumes 2>/dev/null || true

echo "✅ Docker cleanup complete!"
