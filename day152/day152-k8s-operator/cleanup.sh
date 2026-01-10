#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 Starting Docker and system cleanup..."
echo "========================================"

# Stop all running containers
echo "🛑 Stopping all running containers..."
docker stop $(docker ps -q) 2>/dev/null || echo "No running containers to stop"

# Remove all stopped containers
echo "🗑️  Removing stopped containers..."
docker container prune -f

# Remove all unused images
echo "🖼️  Removing unused Docker images..."
docker image prune -a -f

# Remove all unused volumes
echo "💾 Removing unused volumes..."
docker volume prune -f

# Remove all unused networks
echo "🌐 Removing unused networks..."
docker network prune -f

# Remove all unused build cache
echo "📦 Removing unused build cache..."
docker builder prune -f

# System prune (removes everything unused)
echo "🧼 Running system-wide Docker cleanup..."
docker system prune -a -f --volumes

echo ""
echo "✅ Docker cleanup complete!"
echo ""
echo "Summary:"
docker system df
