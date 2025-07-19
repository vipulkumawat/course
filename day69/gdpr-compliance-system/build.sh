#!/bin/bash
set -e

echo "🔧 Building GDPR Compliance System..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build React frontend
echo "🏗️ Building React frontend..."
npm run build

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

echo "✅ Build completed successfully!"
