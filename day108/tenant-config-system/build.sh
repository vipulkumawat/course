#!/bin/bash
set -e

echo "🔨 Building Tenant Configuration System"
echo "====================================="

# Check Python version
echo "🐍 Checking Python version..."
python3.11 --version || (echo "Python 3.11 required" && exit 1)

# Backend setup
echo "🔧 Setting up backend..."
cd backend
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo "🧪 Running backend tests..."
cd ..
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend/src"
python -m pytest backend/tests/ -v

# Frontend setup
echo "⚛️ Setting up frontend..."
cd frontend
npm install
echo "Building frontend..."
npm run build

cd ..
echo "✅ Build completed successfully!"
