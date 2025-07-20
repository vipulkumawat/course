#!/bin/bash

# Log Profiler - Start Script
# This script starts the log profiler application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="log-profiler"
BACKEND_PORT=8000
DASHBOARD_PORT=3000
LOG_DIR="logs"
PID_DIR="pids"
VENV_DIR="venv"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

echo -e "${BLUE}🚀 Starting Log Profiler Application...${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3.11 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install dependencies
echo -e "${BLUE}📥 Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if main application file exists
if [ ! -f "src/main.py" ]; then
    echo -e "${YELLOW}⚠️  Main application file not found. Creating a basic FastAPI app...${NC}"
    mkdir -p src
    cat > src/main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
import psutil
import structlog
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = FastAPI(
    title="Log Profiler",
    description="A comprehensive log analysis and profiling system",
    version="1.0.0"
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Log Profiler Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Log Profiler Dashboard</h1>
                <p class="status">✅ System is running</p>
                <p>Welcome to the Log Profiler application!</p>
            </div>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/metrics">System Metrics</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "log-profiler"
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metrics")

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Log Profiler application starting up")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Log Profiler application shutting down")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
EOF
fi

# Start the FastAPI application
echo -e "${BLUE}🌐 Starting FastAPI server on port $BACKEND_PORT...${NC}"
cd src
nohup python main.py > "../$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "../$PID_DIR/backend.pid"
cd ..

# Wait a moment for the server to start
sleep 3

# Check if the server started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✅ Backend server started successfully (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}📊 Dashboard available at: http://localhost:$BACKEND_PORT${NC}"
    echo -e "${GREEN}📚 API documentation at: http://localhost:$BACKEND_PORT/docs${NC}"
    echo -e "${GREEN}📝 Backend logs: $LOG_DIR/backend.log${NC}"
else
    echo -e "${RED}❌ Failed to start backend server${NC}"
    exit 1
fi

# Optional: Start a simple dashboard server if static files exist
if [ -d "static" ] && [ -f "static/index.html" ]; then
    echo -e "${BLUE}🎨 Starting dashboard server on port $DASHBOARD_PORT...${NC}"
    cd static
    python -m http.server $DASHBOARD_PORT > "../$LOG_DIR/dashboard.log" 2>&1 &
    DASHBOARD_PID=$!
    echo $DASHBOARD_PID > "../$PID_DIR/dashboard.pid"
    cd ..
    
    if kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Dashboard server started successfully (PID: $DASHBOARD_PID)${NC}"
        echo -e "${GREEN}🎨 Dashboard available at: http://localhost:$DASHBOARD_PORT${NC}"
        echo -e "${GREEN}📝 Dashboard logs: $LOG_DIR/dashboard.log${NC}"
    else
        echo -e "${YELLOW}⚠️  Failed to start dashboard server${NC}"
    fi
fi

echo -e "${GREEN}🎉 Log Profiler application started successfully!${NC}"
echo -e "${BLUE}💡 Use './stop.sh' to stop the application${NC}"
echo -e "${BLUE}📋 Use 'tail -f $LOG_DIR/backend.log' to monitor logs${NC}" 