#!/bin/bash

# IOC Scanner - Cleanup Script
# Stops all services, Docker containers, and removes build artifacts

set -e

echo "🧹 IOC Scanner - Cleanup Script"
echo "=================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Stop all services
echo "🛑 Stopping all services..."
pkill -f "python.*src.main" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "node.*start" 2>/dev/null || true
echo "✓ Services stopped"
echo ""

# Stop and remove Docker containers
echo "🐳 Stopping Docker containers..."
if command -v docker &> /dev/null; then
    # Stop all running containers
    if [ "$(docker ps -q)" ]; then
        docker stop $(docker ps -q) 2>/dev/null || true
        echo "✓ Docker containers stopped"
    else
        echo "  No running containers"
    fi
    
    # Remove all containers
    if [ "$(docker ps -aq)" ]; then
        docker rm $(docker ps -aq) 2>/dev/null || true
        echo "✓ Docker containers removed"
    else
        echo "  No containers to remove"
    fi
    
    # Remove unused images
    echo "🗑️  Removing unused Docker images..."
    docker image prune -af --filter "dangling=true" 2>/dev/null || true
    echo "✓ Unused images removed"
    
    # Remove unused volumes
    echo "🗑️  Removing unused Docker volumes..."
    docker volume prune -af 2>/dev/null || true
    echo "✓ Unused volumes removed"
    
    # Remove unused networks
    echo "🗑️  Removing unused Docker networks..."
    docker network prune -af 2>/dev/null || true
    echo "✓ Unused networks removed"
    
    # System prune (optional - removes everything not in use)
    echo "🧹 Running Docker system prune..."
    docker system prune -af --volumes 2>/dev/null || true
    echo "✓ Docker system cleaned"
else
    echo "  Docker not installed or not available"
fi
echo ""

# Remove Python artifacts
echo "🐍 Removing Python artifacts..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
echo "✓ Python artifacts removed"
echo ""

# Remove virtual environment
echo "📦 Removing virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "✓ Virtual environment removed"
else
    echo "  No virtual environment found"
fi
echo ""

# Remove Node.js artifacts
echo "📦 Removing Node.js artifacts..."
if [ -d "web/node_modules" ]; then
    rm -rf web/node_modules
    echo "✓ node_modules removed"
else
    echo "  No node_modules found"
fi

find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "package-lock.json" -delete 2>/dev/null || true
find . -type f -name "yarn.lock" -delete 2>/dev/null || true
echo "✓ Node.js artifacts removed"
echo ""

# Remove Istio files
echo "🔍 Removing Istio files..."
find . -type d -name "*istio*" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*istio*" -delete 2>/dev/null || true
echo "✓ Istio files removed"
echo ""

# Remove log files
echo "📝 Removing log files..."
find . -type f -name "*.log" -delete 2>/dev/null || true
find . -type f -name "*.log.*" -delete 2>/dev/null || true
echo "✓ Log files removed"
echo ""

# Remove build artifacts
echo "🔨 Removing build artifacts..."
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".nuxt" -exec rm -rf {} + 2>/dev/null || true
echo "✓ Build artifacts removed"
echo ""

# Remove IDE files
echo "💻 Removing IDE files..."
find . -type d -name ".idea" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".vscode" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
echo "✓ IDE files removed"
echo ""

# Remove OS files
echo "🖥️  Removing OS files..."
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "Thumbs.db" -delete 2>/dev/null || true
find . -type d -name ".Trash-*" -exec rm -rf {} + 2>/dev/null || true
echo "✓ OS files removed"
echo ""

# Remove temporary files
echo "🗑️  Removing temporary files..."
find . -type f -name "*.tmp" -delete 2>/dev/null || true
find . -type f -name "*.temp" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*.backup" -delete 2>/dev/null || true
echo "✓ Temporary files removed"
echo ""

echo "✅ Cleanup complete!"
echo ""
echo "Remaining files:"
echo "  - Source code"
echo "  - Configuration files"
echo "  - Documentation"
echo ""
