#!/bin/bash

echo "🧪 Testing Windows Event Log Agent"
echo "=================================="

# Activate virtual environment
source venv/bin/activate

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/test_event_agent.py -v

# Run integration tests  
echo "Running integration tests..."
python -m pytest tests/test_integration.py -v

# Test Docker build
echo "Testing Docker build..."
docker build -t windows-event-agent:test .

# Test API endpoints
echo "Testing API endpoints..."
curl -s http://localhost:8080/api/status | python -m json.tool || echo "Dashboard not running"

echo "✅ Tests completed!"
