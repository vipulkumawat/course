#!/bin/bash
set -e

echo "🔨 Building BI Integration System..."

# Activate virtual environment
source venv/bin/activate

# Run syntax check
echo "✓ Checking Python syntax..."
find src -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep -v "^$" || true

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short

echo "✅ Build completed successfully!"
