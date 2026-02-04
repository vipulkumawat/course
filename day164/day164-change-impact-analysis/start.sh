#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Day 164: Change Impact Analysis System"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "   Current directory: $(pwd)"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📌 Using Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Run tests
echo ""
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Check if API server is already running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Stopping existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Check if web server is already running
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "⚠️  Port 3000 is already in use. Stopping existing process..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start API server in background
echo ""
echo "🌐 Starting API server..."
python "$SCRIPT_DIR/src/api_server.py" > api.log 2>&1 &
API_PID=$!
echo "API PID: $API_PID"

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API server is ready"
        break
    fi
    sleep 1
done

# Start web server
echo "🖥️  Starting web dashboard..."
(cd "$SCRIPT_DIR/web/public" && python -m http.server 3000 > ../web.log 2>&1) &
WEB_PID=$!
echo "Web PID: $WEB_PID"

# Wait a moment for web server to start
sleep 2

echo ""
echo "✅ System started successfully!"
echo ""
echo "📍 Access points:"
echo "   API Server: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Web Dashboard: http://localhost:3000"
echo ""
echo "💡 Test the system:"
echo "   curl http://localhost:8000/health"
echo ""
echo "🛑 To stop: ./stop.sh"

# Save PIDs
echo $API_PID > "$SCRIPT_DIR/.api.pid"
echo $WEB_PID > "$SCRIPT_DIR/.web.pid"
