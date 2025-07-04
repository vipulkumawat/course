#!/bin/bash
set -e

echo "🏗️ Building Faceted Search System..."

# Install backend dependencies
cd backend
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
echo "📦 Installing Node.js dependencies..."
npm install

cd ..
echo "✅ Build completed successfully!"
