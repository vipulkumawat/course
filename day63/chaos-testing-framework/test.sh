#!/bin/bash

# Run tests for Chaos Testing Framework
echo "🧪 Running Chaos Testing Framework tests..."

# Activate virtual environment
source venv/bin/activate

# Run different test suites
echo "📋 Running unit tests..."
python -m pytest tests/unit/ -v --tb=short

echo ""
echo "🔗 Running integration tests..."
python -m pytest tests/integration/ -v --tb=short

echo ""
echo "🌪️ Running chaos tests..."
python -m pytest tests/chaos/ -v --tb=short

echo ""
echo "📊 Running all tests with coverage..."
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

echo ""
echo "✅ Testing completed!"
echo "📄 Coverage report: htmlcov/index.html"
