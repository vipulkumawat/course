#!/bin/bash
set -e

echo "🏗️  Building JIRA/ServiceNow Ticket Integration System"
echo "======================================================"

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run code formatting and linting
echo "🔍 Running code quality checks..."
black src/ tests/ --check || true
flake8 src/ tests/ --max-line-length=88 --ignore=E203,W503 || true

# Run type checking
echo "🏷️  Running type checks..."
mypy src/ --ignore-missing-imports || true

# Run unit tests
echo "🧪 Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

# Run integration tests  
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v --tb=short

echo "✅ Build completed successfully!"
