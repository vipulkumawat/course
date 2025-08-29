#!/bin/bash

echo "🚀 Day 100: Starting Automated Scaling System Setup"
echo "=================================================="

# Create and activate virtual environment
echo "📦 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install React dependencies and build
echo "⚛️  Installing React dependencies..."
cd web
npm install
npm run build
cd ..

# Set Python path
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Start the application
echo "🎯 Starting Automated Scaling System..."
echo "📊 Dashboard: http://localhost:8000"
echo "📡 API: http://localhost:8000/api/"
echo ""
echo "Press Ctrl+C to stop the system"

python -m src.main
