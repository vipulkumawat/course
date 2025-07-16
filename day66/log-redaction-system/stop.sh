#!/bin/bash

# Log Redaction System - Stop Script
# This script stops both the FastAPI backend and frontend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PID_DIR="./pids"
LOG_DIR="./logs"

echo -e "${BLUE}🛑 Stopping Log Redaction System...${NC}"

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}🔄 Stopping $service_name (PID: $pid)...${NC}"
            kill $pid
            
            # Wait for graceful shutdown
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  Force killing $service_name...${NC}"
                kill -9 $pid
            fi
            
            rm -f "$pid_file"
            echo -e "${GREEN}✅ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name PID file exists but process not running${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  No PID file found for $service_name${NC}"
    fi
}

# Function to stop service by port
stop_service_by_port() {
    local port=$1
    local service_name=$2
    
    local pids=$(lsof -ti :$port)
    if [ ! -z "$pids" ]; then
        echo -e "${YELLOW}🔄 Stopping $service_name on port $port...${NC}"
        echo "$pids" | xargs kill
        
        # Wait for graceful shutdown
        local count=0
        while lsof -ti :$port > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if lsof -ti :$port > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Force killing processes on port $port...${NC}"
            lsof -ti :$port | xargs kill -9
        fi
        
        echo -e "${GREEN}✅ $service_name stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  No $service_name running on port $port${NC}"
    fi
}

# Create PID directory if it doesn't exist
mkdir -p "$PID_DIR"

# Stop services using PID files first
stop_service "backend"
stop_service "frontend"

# Fallback: stop by port if PID files don't work
stop_service_by_port 8000 "Backend API"
stop_service_by_port 3000 "Frontend"

# Clean up any remaining PID files
rm -f "$PID_DIR"/*.pid

echo -e "${GREEN}🎉 Log Redaction System stopped successfully!${NC}"
echo -e "${BLUE}📁 Logs are available in: $LOG_DIR${NC}" 