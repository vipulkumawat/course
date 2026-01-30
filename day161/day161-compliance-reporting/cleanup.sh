#!/bin/bash

# Cleanup script for Day 161 Compliance Reporting System
# Stops all containers and removes unused Docker resources

set -e

echo "🧹 Starting cleanup process..."
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop and remove containers
echo "🛑 Stopping Docker containers..."
if [ -f "docker-compose.yml" ]; then
    docker-compose down 2>/dev/null || true
    echo "✅ Containers stopped and removed"
else
    echo "⚠️  docker-compose.yml not found, skipping container cleanup"
fi

# Remove Docker images for this project
echo ""
echo "🗑️  Removing Docker images..."
docker images | grep "day161-compliance-reporting" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
echo "✅ Docker images removed"

# Remove unused Docker resources
echo ""
echo "🧹 Cleaning up unused Docker resources..."
docker system prune -f --volumes
echo "✅ Unused Docker resources cleaned"

# Remove Docker networks (if any orphaned)
echo ""
echo "🌐 Cleaning up Docker networks..."
docker network prune -f
echo "✅ Docker networks cleaned"

# Stop any running Python processes related to the project
echo ""
echo "🛑 Stopping any running Python processes..."
pkill -f "python.*src/api/main.py" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true
echo "✅ Python processes stopped"

# Remove Python cache files
echo ""
echo "🗑️  Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo "✅ Python cache files removed"

# Remove pytest cache
echo ""
echo "🗑️  Removing test cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Test cache removed"

# Remove target directories (Rust, Java, etc.)
echo ""
echo "🗑️  Removing target directories..."
find . -type d -name "target" -not -path "./node_modules/*" -exec rm -rf {} + 2>/dev/null || true
echo "✅ Target directories removed"

# Summary
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Summary:"
echo "   - Docker containers: Stopped and removed"
echo "   - Docker images: Removed"
echo "   - Unused Docker resources: Cleaned"
echo "   - Python cache: Removed"
echo "   - Test cache: Removed"
echo "   - Target directories: Removed"
echo ""
echo "💡 To start services again, run: docker-compose up -d"
