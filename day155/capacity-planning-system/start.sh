#!/bin/bash
# Start script for capacity planning system

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Capacity Planning System..."
echo "Working directory: $SCRIPT_DIR"

# Check for existing service on port 8000
if lsof -ti:8000 > /dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ':8000 ' || ss -tuln 2>/dev/null | grep -q ':8000 '; then
    echo "⚠️  Port 8000 is already in use. Checking for existing capacity planning service..."
    EXISTING_PID=$(ps aux | grep -E 'forecast_api|src.api.forecast_api' | grep -v grep | awk '{print $2}' | head -1)
    if [ -n "$EXISTING_PID" ]; then
        echo "Found existing capacity planning service (PID: $EXISTING_PID). Stopping it..."
        kill $EXISTING_PID 2>/dev/null || true
        sleep 2
    else
        echo "⚠️  Different service on port 8000. Please stop it manually or use a different port."
        exit 1
    fi
fi

# Activate virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv/bin/activate. Run setup.sh first."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Start API server in background
echo "Starting API server..."
cd "$SCRIPT_DIR"
python -m src.api.forecast_api > "$SCRIPT_DIR/logs/api.log" 2>&1 &
API_PID=$!
echo $API_PID > "$SCRIPT_DIR/api.pid"

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ API server started (PID: $API_PID)"
        break
    fi
    sleep 1
done

# Start dashboard server on port 3000
echo "Starting dashboard server..."
cd "$SCRIPT_DIR/frontend"
nohup python3 -m http.server 3000 > "$SCRIPT_DIR/logs/dashboard.log" 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > "$SCRIPT_DIR/dashboard.pid"

# Wait for dashboard to be ready
echo "Waiting for dashboard to be ready..."
for i in {1..10}; do
    if curl -s --max-time 2 http://localhost:3000/ > /dev/null 2>&1; then
        echo "✅ Dashboard server started (PID: $DASHBOARD_PID)"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "⚠️  Dashboard server may not be ready yet (check logs/dashboard.log)"
    fi
done

# Get WSL IP address for Windows access
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")

echo ""
echo "✅ Capacity Planning System is running!"
echo ""
echo "📊 Available endpoints (from WSL):"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/"
echo "   Forecast 7 days: http://localhost:8000/api/forecast/7days"
echo "   Capacity Recommendations: http://localhost:8000/api/capacity/recommendations"
echo "   Dashboard: http://localhost:3000/"
echo ""
echo "📊 Available endpoints (from Windows):"
echo "   API Documentation: http://$WSL_IP:8000/docs"
echo "   Dashboard: http://$WSL_IP:3000/"
echo ""
echo "💡 To stop: ./stop.sh"
