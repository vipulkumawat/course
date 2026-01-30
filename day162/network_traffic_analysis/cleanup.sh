#!/bin/bash

# Cleanup script for Network Traffic Analysis project
# Stops containers and removes unused Docker resources

set -e

echo "========================================="
echo "Network Traffic Analysis - Cleanup Script"
echo "========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop application services
echo "1. Stopping application services..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node.*dev" 2>/dev/null || true
sleep 2
echo "   ✓ Application services stopped"
echo ""

# Stop Docker containers
echo "2. Stopping Docker containers..."
if command -v docker &> /dev/null; then
    # Stop all running containers
    if [ "$(docker ps -q)" ]; then
        docker stop $(docker ps -q) 2>/dev/null || true
        echo "   ✓ Stopped running containers"
    else
        echo "   ℹ No running containers"
    fi
    
    # Stop docker-compose services
    if [ -f "docker-compose.yml" ]; then
        docker-compose down 2>/dev/null || true
        echo "   ✓ Stopped docker-compose services"
    fi
else
    echo "   ℹ Docker not installed or not available"
fi
echo ""

# Remove Docker containers
echo "3. Removing Docker containers..."
if command -v docker &> /dev/null; then
    # Remove all stopped containers
    if [ "$(docker ps -aq)" ]; then
        docker rm $(docker ps -aq) 2>/dev/null || true
        echo "   ✓ Removed stopped containers"
    else
        echo "   ℹ No containers to remove"
    fi
else
    echo "   ℹ Docker not available"
fi
echo ""

# Remove unused Docker images
echo "4. Removing unused Docker images..."
if command -v docker &> /dev/null; then
    # Remove dangling images
    docker image prune -f 2>/dev/null || true
    echo "   ✓ Removed dangling images"
    
    # Remove unused images (not used by any container)
    docker image prune -a -f 2>/dev/null || true
    echo "   ✓ Removed unused images"
else
    echo "   ℹ Docker not available"
fi
echo ""

# Remove unused Docker volumes
echo "5. Removing unused Docker volumes..."
if command -v docker &> /dev/null; then
    docker volume prune -f 2>/dev/null || true
    echo "   ✓ Removed unused volumes"
else
    echo "   ℹ Docker not available"
fi
echo ""

# Remove unused Docker networks
echo "6. Removing unused Docker networks..."
if command -v docker &> /dev/null; then
    docker network prune -f 2>/dev/null || true
    echo "   ✓ Removed unused networks"
else
    echo "   ℹ Docker not available"
fi
echo ""

# Clean up build cache
echo "7. Cleaning Docker build cache..."
if command -v docker &> /dev/null; then
    docker builder prune -f 2>/dev/null || true
    echo "   ✓ Cleaned build cache"
else
    echo "   ℹ Docker not available"
fi
echo ""

echo "========================================="
echo "✅ Cleanup complete!"
echo "========================================="
echo ""
echo "Removed:"
echo "  - Stopped containers"
echo "  - Unused images"
echo "  - Unused volumes"
echo "  - Unused networks"
echo "  - Build cache"
echo ""
echo "Note: Application files (node_modules, venv, etc.)"
echo "      should be removed separately using the project cleanup."
echo ""
