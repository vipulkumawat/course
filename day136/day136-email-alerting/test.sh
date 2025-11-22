#!/bin/bash
echo "🧪 Testing Day 136: Email Alerting and Reporting System"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate || { echo "❌ Failed to activate virtual environment"; exit 1; }

# Set PYTHONPATH
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Run unit tests
echo "🔬 Running unit tests..."
python -m pytest tests/ -v --tb=short || { echo "❌ Unit tests failed"; exit 1; }

# Test application startup
echo "🚀 Testing application startup..."
python -c "
import sys
sys.path.insert(0, 'src')
from main import app
from email_service.email_manager import EmailManager
from config.email_config import get_email_config
print('✅ Application imports successful')
"

# Test API endpoints (if server is running)
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "🌐 Testing API endpoints..."
    
    # Test health endpoint
    response=$(curl -s http://localhost:8000/api/health)
    if echo "$response" | grep -q "healthy"; then
        echo "✅ Health endpoint working"
    else
        echo "❌ Health endpoint failed"
        exit 1
    fi
    
    # Test metrics endpoint
    if curl -s http://localhost:8000/api/metrics > /dev/null; then
        echo "✅ Metrics endpoint working"
    else
        echo "❌ Metrics endpoint failed"
        exit 1
    fi
    
    echo "✅ All API tests passed!"
else
    echo "⚠️ Server not running, skipping API tests"
fi

echo "✅ All tests passed!"
