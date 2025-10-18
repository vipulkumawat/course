#!/bin/bash
set -e

source venv/bin/activate

echo "🧪 Running comprehensive test suite..."

# Set Python path
export PYTHONPATH="$(pwd)/backend/src:$PYTHONPATH"

# Run Python tests
echo "Running Python tests..."
cd backend
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

cd ..

# Run frontend tests
echo "Running React tests..."
cd frontend
npm test -- --coverage --watchAll=false
cd ..

echo "✅ All tests completed!"
