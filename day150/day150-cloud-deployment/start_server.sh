#!/bin/bash
# Simple Flask server starter - runs in foreground so you can see errors

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Flask Server"
echo "========================"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Creating it..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📥 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📥 Flask not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Stop any existing Flask processes
echo "🛑 Stopping any existing Flask processes..."
pkill -f "python.*web/app.py" 2>/dev/null || true
pkill -f "flask run" 2>/dev/null || true
sleep 2

# Start Flask
echo ""
echo "🌐 Starting Flask on http://localhost:5000"
echo "🛑 Press Ctrl+C to stop"
echo ""
cd "$SCRIPT_DIR"
python web/app.py
