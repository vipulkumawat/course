#!/bin/bash

echo "🧪 Running tests..."

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PWD}/backend/src:$PYTHONPATH"

# Run backend tests
echo "🔍 Running backend tests..."
cd backend && python -m pytest tests/ -v && cd ..

# Build frontend
echo "🔍 Testing frontend build..."
cd frontend && npm run build && cd ..

echo "✅ All tests passed!"
