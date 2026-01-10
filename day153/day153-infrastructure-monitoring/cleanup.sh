#!/bin/bash

echo "🧹 Docker Cleanup Script"
echo "======================="

# Stop all running containers
echo "🛑 Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

# Remove all stopped containers
echo "🗑️  Removing stopped containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove unused images
echo "🖼️  Removing unused images..."
docker image prune -a -f

# Remove unused volumes
echo "💾 Removing unused volumes..."
docker volume prune -f

# Remove unused networks
echo "🌐 Removing unused networks..."
docker network prune -f

# Remove all unused Docker resources (containers, networks, images, build cache)
echo "🧽 Performing full system prune..."
docker system prune -a -f --volumes

echo ""
echo "✅ Docker cleanup completed!"
