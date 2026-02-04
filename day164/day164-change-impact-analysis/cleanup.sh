#!/bin/bash

# Cleanup script for Docker resources and project artifacts
# This script stops containers and removes unused Docker resources

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 Starting Cleanup Process"
echo "=========================="
echo ""

# Stop any running services first
if [ -f "$SCRIPT_DIR/stop.sh" ]; then
    echo "🛑 Stopping application services..."
    bash "$SCRIPT_DIR/stop.sh"
    echo ""
fi

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
if command -v docker &> /dev/null; then
    # Stop all containers related to this project
    CONTAINERS=$(docker ps -a --filter "name=day164" --filter "name=change-impact" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$CONTAINERS" ]; then
        echo "$CONTAINERS" | xargs docker stop 2>/dev/null || true
        echo "✅ Stopped project containers"
    else
        echo "ℹ️  No project containers found"
    fi
    
    # Stop all running containers (optional - uncomment if needed)
    # docker stop $(docker ps -q) 2>/dev/null || true
    
    # Remove stopped containers
    echo ""
    echo "🗑️  Removing stopped containers..."
    CONTAINERS=$(docker ps -a --filter "name=day164" --filter "name=change-impact" --format "{{.ID}}" 2>/dev/null || true)
    if [ -n "$CONTAINERS" ]; then
        echo "$CONTAINERS" | xargs docker rm 2>/dev/null || true
        echo "✅ Removed project containers"
    fi
    
    # Remove unused images
    echo ""
    echo "🖼️  Removing unused Docker images..."
    docker image prune -f 2>/dev/null || true
    echo "✅ Cleaned unused images"
    
    # Remove unused volumes
    echo ""
    echo "💾 Removing unused Docker volumes..."
    docker volume prune -f 2>/dev/null || true
    echo "✅ Cleaned unused volumes"
    
    # Remove unused networks
    echo ""
    echo "🌐 Removing unused Docker networks..."
    docker network prune -f 2>/dev/null || true
    echo "✅ Cleaned unused networks"
    
    # System prune (removes all unused resources)
    echo ""
    echo "🧼 Running Docker system prune..."
    docker system prune -f 2>/dev/null || true
    echo "✅ Docker system cleanup completed"
else
    echo "⚠️  Docker not found, skipping Docker cleanup"
fi

echo ""
echo "✅ Cleanup completed successfully!"
