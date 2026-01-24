#!/bin/bash

# Cleanup script for SIEM project
# Stops containers and removes unused Docker resources

set -e

echo "🧹 Starting cleanup process..."
echo "======================================================================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop SIEM services
echo ""
echo "🛑 Stopping SIEM services..."
if [ -f "./stop.sh" ]; then
    bash ./stop.sh 2>/dev/null || true
fi

# Kill any remaining uvicorn processes
echo "🛑 Stopping API server processes..."
pkill -f "uvicorn.*server" 2>/dev/null || true
pkill -f "python.*server" 2>/dev/null || true

# Stop and remove Docker containers
echo ""
echo "🐳 Stopping Docker containers..."
docker stop siem-redis 2>/dev/null || true
docker stop $(docker ps -aq --filter "name=siem") 2>/dev/null || true

echo "🐳 Removing Docker containers..."
docker rm siem-redis 2>/dev/null || true
docker rm $(docker ps -aq --filter "name=siem") 2>/dev/null || true

# Remove unused Docker resources
echo ""
echo "🧹 Cleaning up unused Docker resources..."
echo "  - Removing stopped containers..."
docker container prune -f 2>/dev/null || true

echo "  - Removing unused images..."
docker image prune -f 2>/dev/null || true

echo "  - Removing unused volumes..."
docker volume prune -f 2>/dev/null || true

echo "  - Removing unused networks..."
docker network prune -f 2>/dev/null || true

# Remove Python cache files
echo ""
echo "🐍 Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove virtual environment
echo "🐍 Removing virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "  ✓ Removed venv directory"
fi

# Remove node_modules if exists
echo "📦 Removing node_modules..."
if [ -d "node_modules" ]; then
    rm -rf node_modules
    echo "  ✓ Removed node_modules directory"
fi

# Remove Istio files if any
echo "🔍 Checking for Istio files..."
find . -path "*/istio/*" -type f 2>/dev/null | while read file; do
    echo "  Removing: $file"
    rm -f "$file" 2>/dev/null || true
done
find . -name "*istio*" -type f 2>/dev/null | while read file; do
    echo "  Removing: $file"
    rm -f "$file" 2>/dev/null || true
done

# Remove PID files
echo ""
echo "📄 Removing PID files..."
rm -f .api.pid .dashboard.pid server.log 2>/dev/null || true

# Remove temporary files
echo "📄 Removing temporary files..."
rm -f *.log *.pid nohup.out 2>/dev/null || true

# Summary
echo ""
echo "======================================================================"
echo "✅ Cleanup complete!"
echo "======================================================================"
echo ""
echo "Removed:"
echo "  - Python cache files (__pycache__, *.pyc)"
echo "  - Virtual environment (venv)"
echo "  - Docker containers and unused resources"
echo "  - Temporary and PID files"
echo ""
echo "Docker cleanup summary:"
docker system df 2>/dev/null || echo "  (Docker not available)"
echo ""
