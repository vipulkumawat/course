#!/bin/bash

# Log Redaction System - Start Script
# This script starts both the FastAPI backend and frontend services

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
BACKEND_HOST="0.0.0.0"
LOG_DIR="./logs"
PID_DIR="./pids"

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

echo -e "${BLUE}🚀 Starting Log Redaction System...${NC}"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        exit 1
    fi
}

# Function to start backend
start_backend() {
    echo -e "${YELLOW}📡 Starting FastAPI backend on port $BACKEND_PORT...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
        exit 1
    fi
    
    # Activate virtual environment and start backend
    source venv/bin/activate
    
    # Check if main.py exists, if not create a basic one
    if [ ! -f "src/main.py" ]; then
        echo -e "${YELLOW}⚠️  Creating basic FastAPI app...${NC}"
        mkdir -p src
        cat > src/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Log Redaction System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Log Redaction System API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "log-redaction-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
EOF
    fi
    
    # Start backend with uvicorn
    nohup python -m uvicorn src.main:app --host $BACKEND_HOST --port $BACKEND_PORT --reload > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PID_DIR/backend.pid"
    echo -e "${GREEN}✅ Backend started with PID: $BACKEND_PID${NC}"
}

# Function to start frontend
start_frontend() {
    echo -e "${YELLOW}🌐 Starting frontend on port $FRONTEND_PORT...${NC}"
    
    # Check if frontend has package.json
    if [ -f "frontend/package.json" ]; then
        cd frontend
        # Install dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
            npm install
        fi
        
        # Start frontend
        nohup npm start > "../$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > "../$PID_DIR/frontend.pid"
        cd ..
        echo -e "${GREEN}✅ Frontend started with PID: $FRONTEND_PID${NC}"
    else
        echo -e "${YELLOW}⚠️  No frontend package.json found. Creating basic frontend...${NC}"
        mkdir -p frontend
        cd frontend
        
        # Create basic React app structure
        cat > package.json << 'EOF'
{
  "name": "log-redaction-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

        mkdir -p public src
        cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Log Redaction System</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
EOF

        cat > src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

        cat > src/App.js << 'EOF'
import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [apiStatus, setApiStatus] = useState('Checking...');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(response => response.json())
      .then(data => setApiStatus('Connected'))
      .catch(error => setApiStatus('Disconnected'));
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Log Redaction System</h1>
        <p>API Status: {apiStatus}</p>
        <p>Frontend running on port 3000</p>
        <p>Backend running on port 8000</p>
      </header>
    </div>
  );
}

export default App;
EOF

        cat > src/App.css << 'EOF'
.App {
  text-align: center;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.App-header {
  background-color: #282c34;
  padding: 20px;
  color: white;
  border-radius: 8px;
  margin: 20px;
}

h1 {
  color: #61dafb;
}
EOF

        # Install dependencies and start
        npm install
        nohup npm start > "../$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > "../$PID_DIR/frontend.pid"
        cd ..
        echo -e "${GREEN}✅ Frontend started with PID: $FRONTEND_PID${NC}"
    fi
}

# Check ports
check_port $BACKEND_PORT
check_port $FRONTEND_PORT

# Start services
start_backend
sleep 2
start_frontend

echo -e "${GREEN}🎉 Log Redaction System started successfully!${NC}"
echo -e "${BLUE}📊 Services:${NC}"
echo -e "  • Backend API: http://localhost:$BACKEND_PORT"
echo -e "  • Frontend: http://localhost:$FRONTEND_PORT"
echo -e "  • Health Check: http://localhost:$BACKEND_PORT/health"
echo -e "${BLUE}📁 Logs:${NC}"
echo -e "  • Backend logs: $LOG_DIR/backend.log"
echo -e "  • Frontend logs: $LOG_DIR/frontend.log"
echo -e "${BLUE}🛑 To stop: ./stop.sh${NC}" 