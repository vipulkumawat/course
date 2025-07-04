#!/bin/bash
set -e

echo "🧪 Running tests..."

# Run backend tests
echo "🐍 Running Python tests..."
cd backend
python -m pytest tests/ -v

# Run integration tests
cd ../tests/integration
echo "🔌 Running integration tests..."
python -m pytest test_api.py -v

cd ../..
echo "✅ All tests passed!"
