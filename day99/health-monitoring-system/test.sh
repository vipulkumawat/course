#!/bin/bash

echo "🧪 Running Health Monitoring System Tests..."

# Activate virtual environment
source venv/bin/activate

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v

# Run integration tests  
echo "Running integration tests..."
python -m pytest tests/integration/ -v

# Run load tests if available
if [ -f tests/load/test_load.py ]; then
    echo "Running load tests..."
    python -m pytest tests/load/ -v
fi

echo "✅ All tests completed"
