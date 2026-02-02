#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting services from: $SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Kill any existing services
pkill -f "backend/server.py" 2>/dev/null
pkill -f "http.server 8000" 2>/dev/null
sleep 1

# Start WebSocket server
echo "Starting WebSocket server on port 8765..."
cd "$SCRIPT_DIR/backend"
PYTHONPATH="$SCRIPT_DIR/backend:$PYTHONPATH" nohup python server.py "$SCRIPT_DIR/logs/sample.log" > "$SCRIPT_DIR/logs/server.log" 2>&1 &
SERVER_PID=$!
echo "WebSocket server PID: $SERVER_PID"
sleep 2

# Start HTTP server (bind to 0.0.0.0 to be accessible from Windows)
echo "Starting HTTP server on port 8000..."
cd "$SCRIPT_DIR/frontend"
nohup python http_server.py > "$SCRIPT_DIR/logs/http.log" 2>&1 &
HTTP_PID=$!
echo "HTTP server PID: $HTTP_PID"
sleep 2

cd "$SCRIPT_DIR"

# Save PIDs
echo $SERVER_PID > "$SCRIPT_DIR/.server.pid"
echo $HTTP_PID > "$SCRIPT_DIR/.http.pid"

sleep 3

# Verify services are running
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✓ WebSocket server is running (PID: $SERVER_PID)"
else
    echo "✗ WebSocket server failed to start"
    cat "$SCRIPT_DIR/logs/server.log" 2>/dev/null | tail -20
fi

if ps -p $HTTP_PID > /dev/null 2>&1; then
    echo "✓ HTTP server is running (PID: $HTTP_PID)"
else
    echo "✗ HTTP server failed to start"
    cat "$SCRIPT_DIR/logs/http.log" 2>/dev/null | tail -20
fi

# Get WSL IP for Windows access
WSL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

echo ""
echo "========================================="
echo "Services Status:"
echo "========================================="
echo "Dashboard (from WSL): http://localhost:8000"
echo "Dashboard (from Windows): http://$WSL_IP:8000"
echo "WebSocket (from WSL): ws://localhost:8765"
echo "WebSocket (from Windows): ws://$WSL_IP:8765"
echo ""
echo "Note: If connection fails from Windows, try:"
echo "  - http://localhost:8000 (WSL2 port forwarding)"
echo "  - http://$WSL_IP:8000 (direct IP)"
echo ""
echo "To stop services: ./stop.sh"
echo "========================================="
