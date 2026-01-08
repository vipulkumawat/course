#!/bin/bash
# Docker cleanup script for Day 150 Multi-Cloud Deployment
# Stops all containers and removes unused Docker resources

echo "🧹 Starting Docker cleanup..."
echo "================================"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop all running containers
echo ""
echo "🛑 Stopping all running containers..."
if command -v docker >/dev/null 2>&1; then
    RUNNING_CONTAINERS=$(docker ps -q)
    if [ -n "$RUNNING_CONTAINERS" ]; then
        echo "   Found running containers, stopping them..."
        docker stop $RUNNING_CONTAINERS
        echo "✅ All containers stopped"
    else
        echo "   No running containers found"
    fi
    
    # Stop docker-compose services if docker-compose.yml exists
    if [ -f "docker-compose.yml" ]; then
        echo ""
        echo "🛑 Stopping docker-compose services..."
        docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true
        echo "✅ Docker-compose services stopped"
    fi
    
    # Remove all stopped containers
    echo ""
    echo "🗑️  Removing stopped containers..."
    STOPPED_CONTAINERS=$(docker ps -a -q)
    if [ -n "$STOPPED_CONTAINERS" ]; then
        docker rm $STOPPED_CONTAINERS 2>/dev/null || true
        echo "✅ Stopped containers removed"
    else
        echo "   No stopped containers found"
    fi
    
    # Remove unused images
    echo ""
    echo "🗑️  Removing unused Docker images..."
    UNUSED_IMAGES=$(docker images -f "dangling=true" -q)
    if [ -n "$UNUSED_IMAGES" ]; then
        docker rmi $UNUSED_IMAGES 2>/dev/null || true
        echo "✅ Unused images removed"
    else
        echo "   No unused images found"
    fi
    
    # Remove unused volumes
    echo ""
    echo "🗑️  Removing unused Docker volumes..."
    docker volume prune -f 2>/dev/null || true
    echo "✅ Unused volumes removed"
    
    # Remove unused networks
    echo ""
    echo "🗑️  Removing unused Docker networks..."
    docker network prune -f 2>/dev/null || true
    echo "✅ Unused networks removed"
    
    # System prune (optional - removes all unused resources)
    echo ""
    echo "🗑️  Performing system-wide cleanup..."
    docker system prune -f 2>/dev/null || true
    echo "✅ System cleanup completed"
    
    echo ""
    echo "✅ Docker cleanup complete!"
    echo ""
    echo "Remaining Docker resources:"
    echo "  Containers: $(docker ps -a -q | wc -l)"
    echo "  Images: $(docker images -q | wc -l)"
    echo "  Volumes: $(docker volume ls -q | wc -l)"
    echo "  Networks: $(docker network ls -q | wc -l)"
else
    echo "⚠️  Docker is not installed or not available"
    echo "   Skipping Docker cleanup"
fi

echo ""
echo "================================"
echo "✨ Cleanup script completed!"
echo "================================"
