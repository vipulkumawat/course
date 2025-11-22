#!/bin/bash
set -e

echo "🧪 Running Comprehensive Test Suite"
echo "==================================="

# Activate virtual environment
source venv/bin/activate

# Run all tests with coverage
echo "Running tests with coverage..."
python -m pytest tests/ -v \
    --cov=src \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short

echo "📊 Coverage report generated in htmlcov/"
echo "✅ All tests completed!"
