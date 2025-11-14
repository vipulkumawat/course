#!/bin/bash
# Build script for structured logging helpers

echo "🔨 Building Structured Logging Helpers System"
echo "=============================================="

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v --tb=short

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Tests failed!"
    exit 1
fi

# Build documentation
echo "📚 Generating documentation..."
python -c "
from src.core.structured_logger import StructuredLogger
from src.validators.field_validators import ValidatorFactory
print('✅ Core modules imported successfully')
"

echo "🎉 Build completed successfully!"
