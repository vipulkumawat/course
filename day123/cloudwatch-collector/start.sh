#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting CloudWatch Collector..."
echo "Working directory: $SCRIPT_DIR"

# Check if build.sh exists
BUILD_SCRIPT="$SCRIPT_DIR/build.sh"
if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "❌ Error: build.sh not found at $BUILD_SCRIPT"
    exit 1
fi

# Check if virtual environment exists
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running build.sh..."
    if [ -x "$BUILD_SCRIPT" ]; then
        bash "$BUILD_SCRIPT"
    else
        chmod +x "$BUILD_SCRIPT"
        bash "$BUILD_SCRIPT"
    fi
fi

# Check if venv activation script exists
ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "❌ Error: Virtual environment activation script not found at $ACTIVATE_SCRIPT"
    exit 1
fi

# Activate virtual environment
source "$ACTIVATE_SCRIPT"

# Check for .env file
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env file not found at $ENV_FILE. Please create one based on .env.example"
    exit 1
fi

# Check if main.py exists
MAIN_SCRIPT="$SCRIPT_DIR/src/main.py"
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Error: main.py not found at $MAIN_SCRIPT"
    exit 1
fi

# Start collector
echo "Starting collector from $MAIN_SCRIPT..."
python "$MAIN_SCRIPT"
