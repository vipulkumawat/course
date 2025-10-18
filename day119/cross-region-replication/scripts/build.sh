#!/bin/bash
set -e

echo "🚀 Building Cross-Region Replication System..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📍 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt

# Install Node.js dependencies and build frontend
echo "🎨 Building React frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Build completed successfully!"
