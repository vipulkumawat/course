#!/bin/bash

set -e

echo "🚀 Building Tiered Storage System"
echo "================================="

# Create Python virtual environment
echo "📦 Setting up Python environment..."
python3.11 -m venv backend/venv
source backend/venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# Install Node.js dependencies
echo "⚛️ Setting up Frontend environment..."
cd frontend
npm install
cd ..

echo "✅ Build completed successfully!"
echo "🎯 Next steps:"
echo "   1. Run: ./start.sh"
echo "   2. Open: http://localhost:3000"
echo "   3. API: http://localhost:8000"
