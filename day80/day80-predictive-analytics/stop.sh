#!/bin/bash
echo "🛑 Stopping Day 80: Predictive Analytics System"

# Function to check if a process is running
is_process_running() {
    ps -p $1 >/dev/null 2>&1
}

# Function to kill process gracefully
kill_process() {
    local pid=$1
    local name=$2
    
    if is_process_running $pid; then
        echo "🔄 Stopping $name (PID: $pid)..."
        kill $pid 2>/dev/null
        
        # Wait for graceful shutdown
        local count=0
        while is_process_running $pid && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if is_process_running $pid; then
            echo "⚠️  Force killing $name..."
            kill -9 $pid 2>/dev/null
        fi
        
        echo "✅ $name stopped"
    else
        echo "ℹ️  $name is not running"
    fi
}

# Stop API server if PID exists
if [ -f api.pid ]; then
    API_PID=$(cat api.pid)
    kill_process $API_PID "API Server"
    rm -f api.pid
fi

# Stop dashboard if PID exists
if [ -f dashboard.pid ]; then
    DASHBOARD_PID=$(cat dashboard.pid)
    kill_process $DASHBOARD_PID "Dashboard"
    rm -f dashboard.pid
fi

# Stop Celery processes
echo "🔄 Stopping Celery services..."
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "celery.*beat" 2>/dev/null || true

# Stop Redis server
echo "🔄 Stopping Redis server..."
pkill -f redis-server 2>/dev/null || true

# Clean up any remaining processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true

# Deactivate virtual environment if active
if [ -n "$VIRTUAL_ENV" ]; then
    echo "🔧 Deactivating virtual environment..."
    deactivate 2>/dev/null || true
fi

echo ""
echo "✅ System stopped successfully!"
echo "📋 Services stopped:"
echo "   - API Server"
echo "   - Dashboard"
echo "   - Redis Server"
echo "   - Celery Worker"
echo "   - Celery Beat"
echo ""
echo "🚀 To start the system again, run: ./start.sh"
