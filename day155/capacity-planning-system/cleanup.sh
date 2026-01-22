#!/bin/bash
# Cleanup script for Capacity Planning System
# Stops containers and removes unused Docker resources

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 Starting cleanup process..."
echo ""

# Stop application services
echo "1. Stopping application services..."
if [ -f "stop.sh" ]; then
    bash stop.sh 2>/dev/null || true
fi

# Stop Docker containers
echo "2. Stopping Docker containers..."
if command -v docker &> /dev/null; then
    # Stop all containers related to this project
    docker ps -a --filter "name=capacity" --format "{{.ID}}" | xargs -r docker stop 2>/dev/null || true
    docker ps -a --filter "name=planning" --format "{{.ID}}" | xargs -r docker stop 2>/dev/null || true
    
    # Stop containers using docker-compose if it exists
    if [ -f "docker-compose.yml" ]; then
        docker-compose down 2>/dev/null || true
    fi
    
    echo "   ✅ Docker containers stopped"
else
    echo "   ⚠️  Docker not found, skipping container cleanup"
fi

# Remove Docker containers
echo "3. Removing Docker containers..."
if command -v docker &> /dev/null; then
    # Remove stopped containers
    docker ps -a --filter "name=capacity" --format "{{.ID}}" | xargs -r docker rm 2>/dev/null || true
    docker ps -a --filter "name=planning" --format "{{.ID}}" | xargs -r docker rm 2>/dev/null || true
    
    echo "   ✅ Docker containers removed"
fi

# Remove unused Docker images
echo "4. Removing unused Docker images..."
if command -v docker &> /dev/null; then
    # Remove dangling images
    docker image prune -f 2>/dev/null || true
    
    # Remove images related to this project
    docker images --filter "reference=*capacity*" --format "{{.ID}}" | xargs -r docker rmi -f 2>/dev/null || true
    docker images --filter "reference=*planning*" --format "{{.ID}}" | xargs -r docker rmi -f 2>/dev/null || true
    
    echo "   ✅ Unused Docker images removed"
fi

# Remove unused Docker volumes
echo "5. Removing unused Docker volumes..."
if command -v docker &> /dev/null; then
    docker volume prune -f 2>/dev/null || true
    echo "   ✅ Unused Docker volumes removed"
fi

# Remove unused Docker networks
echo "6. Removing unused Docker networks..."
if command -v docker &> /dev/null; then
    docker network prune -f 2>/dev/null || true
    echo "   ✅ Unused Docker networks removed"
fi

# Clean up build cache
echo "7. Cleaning Docker build cache..."
if command -v docker &> /dev/null; then
    docker builder prune -f 2>/dev/null || true
    echo "   ✅ Docker build cache cleaned"
fi

echo ""
echo "✅ Cleanup completed successfully!"
echo ""
echo "Remaining cleanup tasks (manual):"
echo "  - Remove venv/ directory if you want to clean Python virtual environment"
echo "  - Remove node_modules/ if present"
echo "  - Remove .pytest_cache/ directories"
echo "  - Remove __pycache__/ directories"
echo "  - Remove *.pyc files"
