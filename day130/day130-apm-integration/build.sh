#!/bin/bash

echo "🏗️ Building Day 130 APM Integration System"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Check Python version (try 3.11 first, then 3.10, then python3)
if command -v python3.11 > /dev/null; then
    PYTHON_CMD=python3.11
elif command -v python3.10 > /dev/null; then
    PYTHON_CMD=python3.10
elif command -v python3 > /dev/null; then
    PYTHON_CMD=python3
else
    echo "❌ Python 3 not found!"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Create and activate virtual environment
echo "📦 Creating Python virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "⬇️ Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies for frontend
echo "📱 Installing React dependencies..."
cd frontend
npm install
cd ..

# Run tests
echo "🧪 Running Python tests..."
# Add project root to PYTHONPATH for imports
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"
python -m pytest tests/ -v

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Run './start.sh' to start the system"
    echo "  2. Visit http://localhost:3000 for the dashboard"
    echo "  3. API available at http://localhost:8000"
else
    echo "❌ Build failed!"
    exit 1
fi
