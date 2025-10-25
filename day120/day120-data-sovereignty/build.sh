#!/bin/bash
set -e

echo "🏗️  Building Data Sovereignty Compliance System"

# Create and activate virtual environment
echo "📦 Setting up Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
cd tests
python -m pytest -v
cd ..

echo "✅ Build completed successfully!"
