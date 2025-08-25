#!/bin/bash

echo "🧹 Cleaning up project for check-in..."
echo "======================================"

# Stop any running services first
echo "🛑 Stopping any running services..."
./stop.sh 2>/dev/null || true

# Remove virtual environment
echo "🗑️  Removing Python virtual environment..."
rm -rf venv/

# Remove frontend dependencies and build artifacts
echo "🗑️  Removing frontend dependencies and build artifacts..."
cd frontend
rm -rf node_modules/
rm -rf dist/
rm -rf .vite/
rm -f package-lock.json
cd ..

# Remove backend database (this will be recreated on startup)
echo "🗑️  Removing backend database..."
rm -f backend/saved_searches_alerts.db

# Remove any PID files
echo "🗑️  Removing PID files..."
rm -f .backend_pid .frontend_pid

# Remove any log files
echo "🗑️  Removing log files..."
find . -name "*.log" -delete 2>/dev/null || true

# Remove any temporary files
echo "🗑️  Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.cache" -delete 2>/dev/null || true

# Remove OS-specific files
echo "🗑️  Removing OS-specific files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true

# Remove Python cache files
echo "🗑️  Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Remove any coverage reports
echo "🗑️  Removing coverage reports..."
rm -rf htmlcov/
rm -f .coverage
rm -f coverage.xml

echo ""
echo "✅ Cleanup completed successfully!"
echo "📝 Ready for check-in!"
echo ""
echo "To restore the project:"
echo "1. Run: ./start.sh"
echo "2. This will recreate the virtual environment and install dependencies"
