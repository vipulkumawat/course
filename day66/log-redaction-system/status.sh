#!/bin/bash

# Log Redaction System - Status Script
# This script checks the status of both the FastAPI backend and frontend services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
PID_DIR="./pids"

echo -e "${BLUE}📊 Log Redaction System Status${NC}"
echo "=================================="

# Function to check service status
check_service() {
    local service_name=$1
    local port=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    
    echo -e "\n${BLUE}$service_name:${NC}"
    
    # Check if PID file exists and process is running
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ Running (PID: $pid)${NC}"
        else
            echo -e "  ${RED}❌ PID file exists but process not running${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  No PID file found${NC}"
    fi
    
    # Check if port is in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        local port_pid=$(lsof -ti :$port)
        echo -e "  ${GREEN}✅ Port $port is active (PID: $port_pid)${NC}"
    else
        echo -e "  ${RED}❌ Port $port is not in use${NC}"
    fi
    
    # Try to connect to the service
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Health check passed${NC}"
    elif curl -s http://localhost:$port > /dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Service responding${NC}"
    else
        echo -e "  ${RED}❌ Service not responding${NC}"
    fi
}

# Check backend status
check_service "Backend API" $BACKEND_PORT

# Check frontend status
check_service "Frontend" $FRONTEND_PORT

echo -e "\n${BLUE}📋 Quick Commands:${NC}"
echo -e "  • Start: ./start.sh"
echo -e "  • Stop: ./stop.sh"
echo -e "  • Status: ./status.sh"
echo -e "\n${BLUE}🌐 URLs:${NC}"
echo -e "  • Backend API: http://localhost:$BACKEND_PORT"
echo -e "  • Frontend: http://localhost:$FRONTEND_PORT"
echo -e "  • Health Check: http://localhost:$BACKEND_PORT/health" 