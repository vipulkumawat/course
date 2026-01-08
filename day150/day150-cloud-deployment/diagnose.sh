#!/bin/bash
# Diagnostic script to check why Flask isn't working

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Flask Server Diagnostics"
echo "=========================="
echo ""

# Check Python
echo "1. Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python found: $PYTHON_VERSION"
else
    echo "   ❌ Python3 not found!"
    exit 1
fi

# Check venv
echo ""
echo "2. Checking virtual environment..."
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment exists"
    if [ -f "venv/bin/python" ]; then
        VENV_PYTHON=$(venv/bin/python --version)
        echo "   ✅ Venv Python: $VENV_PYTHON"
    else
        echo "   ❌ Venv Python not found"
    fi
else
    echo "   ❌ Virtual environment not found"
    echo "   Run: python3 -m venv venv"
fi

# Check Flask installation
echo ""
echo "3. Checking Flask installation..."
if [ -f "venv/bin/python" ]; then
    if venv/bin/python -c "import flask" 2>/dev/null; then
        FLASK_VERSION=$(venv/bin/python -c "import flask; print(flask.__version__)" 2>/dev/null)
        echo "   ✅ Flask installed: $FLASK_VERSION"
    else
        echo "   ❌ Flask not installed"
        echo "   Run: source venv/bin/activate && pip install -r requirements.txt"
    fi
else
    echo "   ⚠️  Cannot check (venv not found)"
fi

# Check app.py
echo ""
echo "4. Checking Flask app..."
if [ -f "web/app.py" ]; then
    echo "   ✅ app.py exists"
    
    # Try to import it
    if [ -f "venv/bin/python" ]; then
        if venv/bin/python -c "import sys; sys.path.insert(0, '.'); from web.app import app" 2>/dev/null; then
            echo "   ✅ app.py can be imported"
        else
            echo "   ❌ app.py has import errors:"
            venv/bin/python -c "import sys; sys.path.insert(0, '.'); from web.app import app" 2>&1 | head -5
        fi
    fi
else
    echo "   ❌ app.py not found"
fi

# Check template
echo ""
echo "5. Checking template..."
if [ -f "web/templates/dashboard.html" ]; then
    echo "   ✅ dashboard.html exists"
else
    echo "   ❌ dashboard.html not found"
fi

# Check port 5000
echo ""
echo "6. Checking port 5000..."
if command -v lsof &> /dev/null; then
    PORT_CHECK=$(lsof -Pi :5000 -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$PORT_CHECK" ]; then
        echo "   ⚠️  Port 5000 is in use by PID: $PORT_CHECK"
    else
        echo "   ✅ Port 5000 is available"
    fi
elif command -v netstat &> /dev/null; then
    PORT_CHECK=$(netstat -tuln 2>/dev/null | grep ":5000 " || true)
    if [ -n "$PORT_CHECK" ]; then
        echo "   ⚠️  Port 5000 appears to be in use"
    else
        echo "   ✅ Port 5000 is available"
    fi
else
    echo "   ⚠️  Cannot check port (lsof/netstat not available)"
fi

# Check for running Flask processes
echo ""
echo "7. Checking for running Flask processes..."
FLASK_PIDS=$(pgrep -f "python.*web/app.py" 2>/dev/null || true)
if [ -n "$FLASK_PIDS" ]; then
    echo "   ⚠️  Found Flask processes: $FLASK_PIDS"
else
    echo "   ✅ No Flask processes running"
fi

echo ""
echo "=========================="
echo "Diagnostics complete!"
echo ""
echo "To start the server:"
echo "  Foreground: ./start_server.sh"
echo "  Background: ./start_background.sh"
