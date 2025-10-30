#!/bin/bash

echo "🏗️ Building Windows Event Log Agent"
echo "===================================="

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Run tests
echo "Running tests..."
python -m pytest tests/ -v --tb=short

# Build Docker image
echo "Building Docker image..."
docker build -t windows-event-agent:latest .

echo "✅ Build completed successfully!"
echo "Next steps:"
echo "  - Run: ./start.sh (to start the system)"
echo "  - Dashboard: http://localhost:8080"
echo "  - Test: ./test.sh (to run comprehensive tests)"
