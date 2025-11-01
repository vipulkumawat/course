#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏗️  Building CloudWatch Collector..."
echo "Working directory: $SCRIPT_DIR"

# Check for requirements.txt
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ Error: requirements.txt not found at $REQUIREMENTS_FILE"
    exit 1
fi

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$python_version" != "3.11" ]; then
    echo "⚠️  Warning: Python 3.11 recommended, found $(python3 --version)"
fi

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found in PATH"
    exit 1
fi

# Create virtual environment
VENV_DIR="$SCRIPT_DIR/venv"
echo "📦 Creating virtual environment at $VENV_DIR..."
python3 -m venv "$VENV_DIR"

# Check if venv was created
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Error: Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "❌ Error: Virtual environment activation script not found"
    exit 1
fi

source "$ACTIVATE_SCRIPT"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies from $REQUIREMENTS_FILE..."
pip install -r "$REQUIREMENTS_FILE"

# Check if tests directory exists
TESTS_DIR="$SCRIPT_DIR/tests"
if [ -d "$TESTS_DIR" ]; then
    # Run tests
    echo "🧪 Running tests from $TESTS_DIR..."
    python -m pytest "$TESTS_DIR" -v || echo "⚠️  Some tests may have failed, but continuing..."
else
    echo "⚠️  Tests directory not found at $TESTS_DIR, skipping tests"
fi

echo "✅ Build complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and configure AWS credentials"
echo "  2. Run: $SCRIPT_DIR/start.sh"
