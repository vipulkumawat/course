#!/bin/bash
# Start services script that ensures they stay running

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Starting Network Traffic Analysis System"
echo "========================================="

# Kill any existing processes
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run setup first."
    exit 1
fi

# Start backend
echo "Starting backend on http://0.0.0.0:8000..."
cd "$SCRIPT_DIR"
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend
sleep 5

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo "❌ Backend failed to start. Check backend.log"
    cat backend.log
    exit 1
fi

# Test backend
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠ Backend may not be ready yet"
fi

# Start frontend
echo "Starting frontend on http://0.0.0.0:3000..."
cd "$SCRIPT_DIR/frontend"

# Use setsid to detach process properly
setsid npm run dev -- --host 0.0.0.0 > ../frontend.log 2>&1 < /dev/null &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to start
sleep 10

# Check if frontend process is running
if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
    # Check if vite is running (might be child process)
    if pgrep -f "vite" > /dev/null; then
        echo "✅ Frontend is running (vite process found)"
    else
        echo "❌ Frontend failed to start. Check frontend.log"
        cat ../frontend.log | tail -30
        echo ""
        echo "Trying to start frontend manually..."
        cd "$SCRIPT_DIR/frontend"
        npm run dev -- --host 0.0.0.0 &
        sleep 5
    fi
else
    echo "✅ Frontend process is running"
fi

# Check ports
echo ""
echo "Checking ports..."
ss -tuln | grep -E ':(8000|3000)' || echo "⚠ Ports may not be listening yet"

echo ""
echo "========================================="
echo "✅ Services started!"
echo "========================================="
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:  $SCRIPT_DIR/backend.log"
echo "  Frontend: $SCRIPT_DIR/frontend.log"
echo ""
echo "To stop: pkill -f 'uvicorn main:app' && pkill -f 'vite'"
echo ""
