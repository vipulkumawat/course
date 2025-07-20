#!/bin/bash

# Log Profiler - Stop Script
# This script stops the log profiler application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PID_DIR="pids"
LOG_DIR="logs"

echo -e "${BLUE}🛑 Stopping Log Profiler Application...${NC}"

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${BLUE}🔄 Stopping $service_name (PID: $pid)...${NC}"
            kill "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force killing $service_name (PID: $pid)...${NC}"
                kill -9 "$pid"
            fi
            
            echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name process not running (PID: $pid)${NC}"
        fi
        
        # Remove PID file
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Stop backend server
stop_service "backend"

# Stop dashboard server (if running)
stop_service "dashboard"

# Check for any remaining processes
echo -e "${BLUE}🔍 Checking for any remaining log profiler processes...${NC}"
remaining_pids=$(pgrep -f "log-profiler\|main.py" || true)

if [ -n "$remaining_pids" ]; then
    echo -e "${YELLOW}⚠️  Found remaining processes: $remaining_pids${NC}"
    echo "$remaining_pids" | while read pid; do
        if [ -n "$pid" ]; then
            echo -e "${BLUE}🔄 Stopping remaining process (PID: $pid)...${NC}"
            kill "$pid" 2>/dev/null || true
        fi
    done
else
    echo -e "${GREEN}✅ No remaining processes found${NC}"
fi

# Clean up PID directory if empty
if [ -d "$PID_DIR" ] && [ -z "$(ls -A $PID_DIR)" ]; then
    rmdir "$PID_DIR"
    echo -e "${GREEN}✅ Cleaned up empty PID directory${NC}"
fi

echo -e "${GREEN}🎉 Log Profiler application stopped successfully!${NC}"
echo -e "${BLUE}💡 Use './start.sh' to start the application again${NC}" 