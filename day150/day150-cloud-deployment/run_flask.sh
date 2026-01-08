#!/bin/bash
# Simple Flask runner - ensures venv is activated and runs Flask

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run ./start.sh first."
    exit 1
fi

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start Flask
echo "🚀 Starting Flask on http://localhost:5000"
echo "🛑 Press Ctrl+C to stop"
echo ""
cd "$SCRIPT_DIR"
python web/app.py
