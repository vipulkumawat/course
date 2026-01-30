#!/bin/bash

echo "🚀 Starting Day 161: Security Compliance Reporting System"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3.11 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
mkdir -p data/{logs,evidence,reports}

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Start API server
echo "🌐 Starting API server..."
python src/api/main.py &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
sleep 5

# Generate test data
echo "📊 Generating test security events..."
python scripts/generate_test_data.py

echo ""
echo "✅ System started successfully!"
echo "📊 API: http://localhost:8000"
echo "📊 Dashboard: http://localhost:3000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

wait $API_PID
