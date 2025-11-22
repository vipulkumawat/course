#!/bin/bash
echo "🏗️ Building Day 136: Email Alerting and Reporting System"

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate || { echo "❌ Failed to activate virtual environment"; exit 1; }

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python -m pytest tests/ -v -x || { echo "❌ Tests failed"; exit 1; }

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t email-alerting-system:latest . || { echo "❌ Docker build failed"; exit 1; }

echo "✅ Build completed successfully!"
