#!/bin/bash

# Project cleanup script - Removes generated files and caches
# This removes node_modules, venv, cache files, etc.

set -e

echo "========================================="
echo "Project Cleanup Script"
echo "========================================="
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Remove node_modules
echo "1. Removing node_modules..."
if [ -d "frontend/node_modules" ]; then
    rm -rf frontend/node_modules
    echo "   ✓ Removed frontend/node_modules"
else
    echo "   ℹ node_modules not found"
fi
echo ""

# Remove venv
echo "2. Removing Python virtual environment..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "   ✓ Removed venv/"
else
    echo "   ℹ venv not found"
fi
echo ""

# Remove pytest cache
echo "3. Removing pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
if [ $? -eq 0 ]; then
    echo "   ✓ Removed .pytest_cache directories"
else
    echo "   ℹ No .pytest_cache found"
fi
echo ""

# Remove __pycache__ directories
echo "4. Removing __pycache__ directories..."
find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
echo "   ✓ Removed __pycache__ directories"
echo ""

# Remove .pyc, .pyo, .pyd files
echo "5. Removing Python cache files..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
echo "   ✓ Removed .pyc, .pyo, .pyd files"
echo ""

# Remove Istio files
echo "6. Removing Istio files..."
find . -type d -name "istio*" -exec rm -rf {} + 2>/dev/null || true
find . -type f \( -name "*istio*.yaml" -o -name "*istio*.yml" \) -delete 2>/dev/null || true
echo "   ✓ Removed Istio files"
echo ""

# Remove log files
echo "7. Removing log files..."
rm -f *.log backend.log frontend.log startup.log 2>/dev/null || true
rm -f logs/*.log 2>/dev/null || true
echo "   ✓ Removed log files"
echo ""

# Remove PID files
echo "8. Removing PID files..."
rm -f .backend.pid .frontend.pid *.pid 2>/dev/null || true
echo "   ✓ Removed PID files"
echo ""

# Remove temporary files
echo "9. Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true
echo "   ✓ Removed temporary files"
echo ""

# Remove frontend build artifacts
echo "10. Removing frontend build artifacts..."
rm -rf frontend/dist 2>/dev/null || true
rm -rf frontend/build 2>/dev/null || true
rm -rf frontend/.vite 2>/dev/null || true
echo "   ✓ Removed frontend build artifacts"
echo ""

echo "========================================="
echo "✅ Project cleanup complete!"
echo "========================================="
echo ""
echo "Removed:"
echo "  - node_modules/"
echo "  - venv/"
echo "  - .pytest_cache/"
echo "  - __pycache__/ directories"
echo "  - *.pyc, *.pyo, *.pyd files"
echo "  - Istio files"
echo "  - Log files"
echo "  - PID files"
echo "  - Temporary files"
echo "  - Frontend build artifacts"
echo ""
echo "Note: Source code and configuration files are preserved."
echo ""
