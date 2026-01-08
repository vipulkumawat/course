#!/bin/bash
# Start script for Day 150 Multi-Cloud Deployment

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Day 150: Multi-Cloud Deployment Templates"
echo "====================================================="
echo "Working directory: $SCRIPT_DIR"

# Check for duplicate services
echo ""
echo "🔍 Checking for duplicate services..."
FLASK_PIDS=$(pgrep -f "python.*web/app.py" || true)
if [ -n "$FLASK_PIDS" ]; then
    echo "⚠️  Found existing Flask processes: $FLASK_PIDS"
    echo "   Stopping duplicate services..."
    pkill -f "python.*web/app.py" || true
    sleep 2
fi

# Verify required files exist
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found in $SCRIPT_DIR"
    exit 1
fi

if [ ! -f "web/app.py" ]; then
    echo "❌ Error: web/app.py not found in $SCRIPT_DIR"
    exit 1
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    if command -v python3.11 &> /dev/null; then
        python3.11 -m venv venv 2>/dev/null || python3 -m venv venv 2>/dev/null || echo "⚠️  Warning: Could not create venv, using system Python"
    else
        python3 -m venv venv 2>/dev/null || echo "⚠️  Warning: Could not create venv, using system Python"
    fi
fi

echo "🔧 Setting up Python environment..."
if [ -f "venv/bin/python" ] || [ -f "venv/bin/python3" ]; then
    if [ -f "venv/bin/python" ]; then
        VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
    else
        VENV_PYTHON="$SCRIPT_DIR/venv/bin/python3"
    fi
    # Use python -m pip for better compatibility
    VENV_PIP="$VENV_PYTHON -m pip"
    echo "✅ Using venv Python: $VENV_PYTHON"
else
    echo "⚠️  Virtual environment not available, using system Python"
    VENV_PYTHON="python3"
    VENV_PIP="python3 -m pip"
fi

# Install dependencies
echo "📥 Installing Python dependencies..."
if ! $VENV_PYTHON -m pip --version > /dev/null 2>&1 && ! command -v pip3 > /dev/null 2>&1 && ! command -v pip > /dev/null 2>&1; then
    echo "❌ Error: pip is not available. Please install pip first:"
    echo "   sudo apt-get install python3-pip"
    echo "   Or: curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py --user"
    exit 1
fi

# Try to upgrade pip (non-fatal if it fails)
$VENV_PIP install --upgrade pip --break-system-packages > /dev/null 2>&1 || echo "⚠️  Warning: pip upgrade failed (continuing...)"

# Install dependencies
# Use --break-system-packages if venv is incomplete (symlinked to system Python)
BREAK_FLAG=""
if [ ! -f "$SCRIPT_DIR/venv/pyvenv.cfg" ] || ! grep -q "include-system-site-packages = false" "$SCRIPT_DIR/venv/pyvenv.cfg" 2>/dev/null; then
    BREAK_FLAG="--break-system-packages"
    echo "⚠️  Using --break-system-packages (venv may be incomplete)"
fi

if ! $VENV_PIP install $BREAK_FLAG -r requirements.txt > /dev/null 2>&1; then
    echo "❌ Error: Failed to install dependencies"
    echo "   Trying with verbose output..."
    $VENV_PIP install $BREAK_FLAG -r requirements.txt || {
        echo "❌ Error: Failed to install dependencies. Please check your Python/pip setup."
        exit 1
    }
fi

# Run tests
echo ""
echo "🧪 Running tests..."
$VENV_PYTHON -m pytest tests/ -v || echo "⚠️  Warning: Some tests failed (this may be expected)"

# Start web dashboard
echo ""
echo "🌐 Starting deployment dashboard..."
echo "Dashboard will be available at: http://localhost:5000"
echo ""

# Check if port 5000 is already in use
PORT_IN_USE=false
if command -v lsof >/dev/null 2>&1 && lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PORT_IN_USE=true
elif command -v netstat >/dev/null 2>&1 && netstat -tuln 2>/dev/null | grep -q ":5000 " ; then
    PORT_IN_USE=true
fi

if [ "$PORT_IN_USE" = true ]; then
    echo "⚠️  Port 5000 is already in use."
    echo "   If Flask is already running, you can access it at http://localhost:5000"
    echo "   To restart, run: ./stop.sh first"
else
    echo "🚀 Starting Flask application..."
    cd "$SCRIPT_DIR"
    
    # Create log file in project directory (more reliable than /tmp)
    LOG_FILE="$SCRIPT_DIR/flask.log"
    PID_FILE="$SCRIPT_DIR/flask.pid"
    
    # Use nohup to ensure process survives
    nohup "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/web/app.py" > "$LOG_FILE" 2>&1 &
    WEB_PID=$!
    echo $WEB_PID > "$PID_FILE"
    echo "✅ Dashboard started with PID: $WEB_PID"
    
    # Wait a moment for server to start
    sleep 5
    
    # Verify server is running
    if ! kill -0 $WEB_PID 2>/dev/null; then
        echo "❌ Error: Dashboard failed to start"
        echo "Check logs: cat $LOG_FILE"
        cat "$LOG_FILE" 2>/dev/null || true
        rm -f "$PID_FILE"
        exit 1
    fi
    
    # Check if port is actually listening
    PORT_LISTENING=false
    if command -v lsof >/dev/null 2>&1; then
        if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT_LISTENING=true
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":5000 " ; then
            PORT_LISTENING=true
        fi
    fi
    
    if [ "$PORT_LISTENING" = true ]; then
        echo "✅ Server is listening on port 5000"
    else
        echo "⚠️  Warning: Server process exists but port may not be listening yet"
        echo "   Check logs: cat $LOG_FILE"
        echo "   Waiting a bit more..."
        sleep 3
        if command -v lsof >/dev/null 2>&1 && lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "✅ Server is now listening on port 5000"
        else
            echo "⚠️  Port still not listening. Check logs: cat $LOG_FILE"
        fi
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Available commands:"
echo "  - Access dashboard: http://localhost:5000"
echo "  - Deploy to AWS Dev: python $SCRIPT_DIR/scripts/deploy.py --environment dev --cloud aws"
echo "  - Run tests: python -m pytest $SCRIPT_DIR/tests/ -v"
echo "  - Stop: $SCRIPT_DIR/stop.sh"
echo ""

# Keep script running if we started the server
if [ -n "$WEB_PID" ]; then
    echo ""
    echo "💡 Tip: The server is running in the background."
    echo "   Logs: tail -f $LOG_FILE"
    echo "   Stop: $SCRIPT_DIR/stop.sh or kill $WEB_PID"
    echo ""
    echo "🌐 Access dashboard at: http://localhost:5000"
    echo ""
fi
