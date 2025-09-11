#!/bin/bash
set -e

echo "🔨 Building Day 107: Tenant Isolation System"
echo "============================================="

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
python3.11 -m venv venv || python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt

# Run backend tests
echo "🧪 Running backend tests..."
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
python -m pytest tests/ -v --tb=short

cd ..

# Setup frontend
echo "⚛️ Setting up frontend..."
cd frontend
npm install
npm run build

cd ..

echo "✅ Build completed successfully!"
echo "🚀 Run './scripts/start.sh' to start the system"
