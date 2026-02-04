#!/bin/bash
set -e
echo "🚀 Starting SLA Monitoring System..."

# Check for duplicate services
if [ -f "check_services.sh" ]; then
    if bash check_services.sh >/dev/null 2>&1; then
        echo "✅ No duplicate services found"
    else
        echo "⚠️  Warning: Found running services. Stopping them first..."
        if [ -f "stop.sh" ]; then
            bash stop.sh
            sleep 2
        fi
    fi
fi

# Start Redis if not running
if ! redis-cli ping >/dev/null 2>&1; then
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Setup Python environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run tests
echo -e "\n🧪 Running tests..."
python -m pytest tests/ -v

# Start system
echo -e "\n🎯 Starting SLA monitoring..."
echo "📊 Dashboard will be available at: http://localhost:8000"
echo "⏳ Waiting for metrics to be collected (this may take 10-20 seconds)..."
python -m src.main
