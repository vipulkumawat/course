#!/bin/bash

set -e

echo "🛑 Stopping Day 57: Log Search with Ranking System (Native)"

# Function to kill processes by port
kill_process_by_port() {
    local port=$1
    local process_name=$2
    
    # Find PID using the port
    local pid=$(lsof -ti:$port 2>/dev/null)
    
    if [ ! -z "$pid" ]; then
        echo "🛑 Stopping $process_name (PID: $pid) on port $port..."
        kill $pid 2>/dev/null || true
        
        # Wait a moment and force kill if still running
        sleep 2
        if lsof -ti:$port >/dev/null 2>&1; then
            echo "⚠️  Force killing $process_name on port $port..."
            kill -9 $pid 2>/dev/null || true
        fi
    else
        echo "ℹ️  No $process_name process found on port $port"
    fi
}

# Function to kill processes by name pattern
kill_process_by_name() {
    local name_pattern=$1
    local process_description=$2
    
    # Find PIDs by name pattern
    local pids=$(pgrep -f "$name_pattern" 2>/dev/null)
    
    if [ ! -z "$pids" ]; then
        echo "🛑 Stopping $process_description processes..."
        echo "$pids" | while read pid; do
            if [ ! -z "$pid" ]; then
                echo "  Killing PID: $pid"
                kill $pid 2>/dev/null || true
            fi
        done
        
        # Wait a moment and force kill if still running
        sleep 2
        local remaining_pids=$(pgrep -f "$name_pattern" 2>/dev/null)
        if [ ! -z "$remaining_pids" ]; then
            echo "⚠️  Force killing remaining $process_description processes..."
            echo "$remaining_pids" | while read pid; do
                if [ ! -z "$pid" ]; then
                    echo "  Force killing PID: $pid"
                    kill -9 $pid 2>/dev/null || true
                fi
            done
        fi
    else
        echo "ℹ️  No $process_description processes found"
    fi
}

echo "🔍 Looking for running services..."

# Stop backend (Python/FastAPI) on port 8000
kill_process_by_port 8000 "Backend (FastAPI)"

# Stop frontend (React) on port 3000
kill_process_by_port 3000 "Frontend (React)"

# Additional cleanup by process name patterns
kill_process_by_name "python.*main.py" "Python backend"
kill_process_by_name "node.*react-scripts" "React development server"
kill_process_by_name "uvicorn.*main:app" "Uvicorn server"

# Check if any services are still running
echo "🔍 Checking if services are still running..."

if lsof -ti:8000 >/dev/null 2>&1; then
    echo "⚠️  Backend is still running on port 8000"
else
    echo "✅ Backend stopped"
fi

if lsof -ti:3000 >/dev/null 2>&1; then
    echo "⚠️  Frontend is still running on port 3000"
else
    echo "✅ Frontend stopped"
fi

echo -e "\n✅ All services stopped successfully!"
echo "📊 To start services again, run: ./start-native.sh" 