#!/bin/bash

# Day 72: Adaptive Batching System - Stop Script
# Stops both backend (FastAPI) and frontend (React) services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PID_DIR=".pids"
LOG_DIR="logs"

echo -e "${BLUE}🛑 Stopping Adaptive Batching System...${NC}"

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        
        if kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}🔄 Stopping $service_name (PID: $pid)...${NC}"
            
            # Try graceful shutdown first
            kill $pid
            
            # Wait for graceful shutdown (5 seconds)
            local count=0
            while kill -0 $pid 2>/dev/null && [ $count -lt 5 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}⚠️  Force stopping $service_name...${NC}"
                kill -9 $pid 2>/dev/null || true
                sleep 1
            fi
            
            # Verify process is stopped
            if kill -0 $pid 2>/dev/null; then
                echo -e "${RED}❌ Failed to stop $service_name${NC}"
                return 1
            else
                echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
                rm -f "$pid_file"
                return 0
            fi
        else
            echo -e "${YELLOW}⚠️  $service_name is not running (PID: $pid)${NC}"
            rm -f "$pid_file"
            return 0
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
        return 0
    fi
}

# Function to check if any services are still running
check_running_services() {
    local running=false
    
    # Check backend
    if [ -f "$PID_DIR/backend.pid" ]; then
        local backend_pid=$(cat "$PID_DIR/backend.pid")
        if kill -0 $backend_pid 2>/dev/null; then
            echo -e "${RED}❌ Backend is still running (PID: $backend_pid)${NC}"
            running=true
        fi
    fi
    
    # Check frontend
    if [ -f "$PID_DIR/frontend.pid" ]; then
        local frontend_pid=$(cat "$PID_DIR/frontend.pid")
        if kill -0 $frontend_pid 2>/dev/null; then
            echo -e "${RED}❌ Frontend is still running (PID: $frontend_pid)${NC}"
            running=true
        fi
    fi
    
    if [ "$running" = true ]; then
        return 1
    else
        return 0
    fi
}

# Function to cleanup orphaned processes
cleanup_orphaned_processes() {
    echo -e "${YELLOW}🧹 Cleaning up orphaned processes...${NC}"
    
    # Kill any remaining uvicorn processes on port 8000
    local uvicorn_pids=$(lsof -ti:8000 2>/dev/null || true)
    if [ ! -z "$uvicorn_pids" ]; then
        echo -e "${YELLOW}⚠️  Found orphaned uvicorn processes: $uvicorn_pids${NC}"
        echo $uvicorn_pids | xargs kill -9 2>/dev/null || true
    fi
    
    # Kill any remaining node processes on port 3000
    local node_pids=$(lsof -ti:3000 2>/dev/null || true)
    if [ ! -z "$node_pids" ]; then
        echo -e "${YELLOW}⚠️  Found orphaned node processes: $node_pids${NC}"
        echo $node_pids | xargs kill -9 2>/dev/null || true
    fi
}

# Main execution
main() {
    # Check if PID directory exists
    if [ ! -d "$PID_DIR" ]; then
        echo -e "${YELLOW}⚠️  No PID directory found. Services may not be running.${NC}"
        cleanup_orphaned_processes
        return 0
    fi
    
    # Stop services
    local backend_stopped=false
    local frontend_stopped=false
    
    # Stop backend
    if stop_service "backend"; then
        backend_stopped=true
    fi
    
    # Stop frontend
    if stop_service "frontend"; then
        frontend_stopped=true
    fi
    
    # Cleanup orphaned processes
    cleanup_orphaned_processes
    
    # Final verification
    if check_running_services; then
        echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
        
        # Clean up PID directory if empty
        if [ -d "$PID_DIR" ] && [ -z "$(ls -A $PID_DIR)" ]; then
            rmdir "$PID_DIR"
            echo -e "${BLUE}🗑️  Cleaned up PID directory${NC}"
        fi
        
        # Show log locations
        if [ -d "$LOG_DIR" ]; then
            echo -e "${BLUE}📝 Logs available in: $LOG_DIR/${NC}"
        fi
        
        echo -e "${YELLOW}🚀 Use './start.sh' to start the services again${NC}"
    else
        echo -e "${RED}❌ Some services could not be stopped${NC}"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}⚠️  Interrupted. Cleaning up...${NC}"; cleanup_orphaned_processes; exit 1' INT TERM

# Run main function
main "$@" 