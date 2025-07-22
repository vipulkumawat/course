#!/bin/bash

# Day 72: Adaptive Batching System - Start Script
# Starts both backend (FastAPI) and frontend (React) services

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
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
LOG_DIR="logs"
PID_DIR=".pids"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

echo -e "${BLUE}🚀 Starting Adaptive Batching System...${NC}"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}📡 Starting FastAPI backend...${NC}"
    
    if ! check_port $BACKEND_PORT; then
        return 1
    fi
    
    cd "$BACKEND_DIR"
    
    # Check if virtual environment exists, create if not
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}🔧 Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Start FastAPI server
    nohup uvicorn src.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "../$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "../$PID_DIR/backend.pid"
    
    cd ..
    
    # Wait a moment for the server to start
    sleep 3
    
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Backend started successfully (PID: $BACKEND_PID, Port: $BACKEND_PORT)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start backend${NC}"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}🌐 Starting React frontend...${NC}"
    
    if ! check_port $FRONTEND_PORT; then
        return 1
    fi
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Start React development server
    nohup npm start > "../$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "../$PID_DIR/frontend.pid"
    
    cd ..
    
    # Wait a moment for the server to start
    sleep 5
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Frontend started successfully (PID: $FRONTEND_PID, Port: $FRONTEND_PORT)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start frontend${NC}"
        return 1
    fi
}

# Main execution
main() {
    # Check if services are already running
    if [ -f "$PID_DIR/backend.pid" ] && kill -0 $(cat "$PID_DIR/backend.pid") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Backend is already running${NC}"
    else
        start_backend
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to start backend. Check logs at $LOG_DIR/backend.log${NC}"
            exit 1
        fi
    fi
    
    if [ -f "$PID_DIR/frontend.pid" ] && kill -0 $(cat "$PID_DIR/frontend.pid") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Frontend is already running${NC}"
    else
        start_frontend
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Failed to start frontend. Check logs at $LOG_DIR/frontend.log${NC}"
            # Stop backend if frontend fails
            if [ -f "$PID_DIR/backend.pid" ]; then
                kill $(cat "$PID_DIR/backend.pid") 2>/dev/null || true
                rm -f "$PID_DIR/backend.pid"
            fi
            exit 1
        fi
    fi
    
    echo -e "${GREEN}🎉 Adaptive Batching System started successfully!${NC}"
    echo -e "${BLUE}📊 Backend API: http://localhost:$BACKEND_PORT${NC}"
    echo -e "${BLUE}🌐 Frontend Dashboard: http://localhost:$FRONTEND_PORT${NC}"
    echo -e "${BLUE}📋 Health Check: http://localhost:$BACKEND_PORT/api/health${NC}"
    echo -e "${YELLOW}📝 Logs available in: $LOG_DIR/${NC}"
    echo -e "${YELLOW}🛑 Use './stop.sh' to stop the services${NC}"
}

# Run main function
main "$@" 