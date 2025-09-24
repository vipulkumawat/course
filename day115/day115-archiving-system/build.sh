#!/bin/bash
set -e

echo "🔨 Building Day 115 Archival System..."

# Activate virtual environment
source venv/bin/activate

echo "🧪 Running unit tests..."
python -m pytest tests/unit/ -v

echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v

echo "📦 Creating sample data..."
mkdir -p logs
echo '{"timestamp": "2025-05-01T10:00:00Z", "level": "INFO", "service": "api", "message": "Test log"}' > logs/sample.log

echo "✅ Build completed successfully!"
echo "📊 Dashboard will be available at: http://localhost:8001"
echo "🚀 Run './start.sh' to start the system"
