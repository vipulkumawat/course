#!/bin/bash

echo "🧹 Starting Docker cleanup..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Remove node_modules if it exists
if [ -d "web/node_modules" ]; then
    echo "Removing node_modules..."
    # Try to change ownership first
    chown -R $(whoami):$(whoami) web/node_modules 2>/dev/null || true
    # Try removal
    if rm -rf web/node_modules 2>/dev/null; then
        echo "✅ node_modules removed"
    else
        echo "⚠️  node_modules owned by root - attempting with sudo..."
        sudo rm -rf web/node_modules 2>/dev/null && echo "✅ node_modules removed with sudo" || {
            echo "⚠️  Could not remove node_modules (permission denied)"
            echo "   Please run manually: sudo rm -rf web/node_modules"
        }
    fi
fi

# Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

# Remove all stopped containers
echo "Removing stopped containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove all unused images
echo "Removing unused images..."
docker image prune -a -f 2>/dev/null || echo "No unused images to remove"

# Remove all unused volumes
echo "Removing unused volumes..."
docker volume prune -f 2>/dev/null || echo "No unused volumes to remove"

# Remove all unused networks
echo "Removing unused networks..."
docker network prune -f 2>/dev/null || echo "No unused networks to remove"

# Remove all unused build cache
echo "Removing unused build cache..."
docker builder prune -a -f 2>/dev/null || echo "No build cache to remove"

# Stop docker-compose services if running
echo "Stopping docker-compose services..."
docker-compose down 2>/dev/null || echo "No docker-compose services running"

# System prune (removes all unused containers, networks, images, and build cache)
echo "Running system-wide Docker cleanup..."
docker system prune -a -f --volumes 2>/dev/null || echo "Docker system prune completed"

echo ""
echo "✅ Docker cleanup completed!"
echo ""
echo "Summary:"
docker system df 2>/dev/null || echo "Docker system info unavailable"
