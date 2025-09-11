#!/bin/bash
set -e

echo "🧪 Running Day 107 Test Suite"
echo "============================="

# Activate virtual environment
source venv/bin/activate

# Backend tests
echo "🔬 Running backend tests..."
cd backend
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

cd ..

# Integration tests
echo "🔗 Running integration tests..."
python scripts/integration_test.py

echo "✅ All tests passed!"
