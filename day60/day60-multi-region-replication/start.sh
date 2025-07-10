#!/bin/bash

# Day 60: Multi-Region Log Replication System - Start Script
# ===========================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/regions/us-east-1
    mkdir -p data/regions/us-west-2
    mkdir -p data/regions/eu-west-1
    mkdir -p config/regions
    mkdir -p scripts/utils
    
    print_success "Directories created"
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    if [ -d "tests" ] && [ "$(ls -A tests 2>/dev/null)" ]; then
        python -m pytest tests/ -v
        print_success "Tests completed"
    else
        print_warning "No tests found, skipping test execution"
    fi
}

# Function to verify system requirements
verify_system() {
    print_status "Verifying system requirements..."
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python version: $python_version"
    
    # Check if required commands exist
    local required_commands=("python3" "pip" "redis-server" "docker")
    
    for cmd in "${required_commands[@]}"; do
        if command_exists "$cmd"; then
            print_success "$cmd is available"
        else
            print_warning "$cmd is not available (some features may not work)"
        fi
    done
    
    # Check available ports
    local required_ports=(8000 8001 8002 6379 5432)
    
    for port in "${required_ports[@]}"; do
        if check_port $port; then
            print_warning "Port $port is already in use"
        else
            print_success "Port $port is available"
        fi
    done
}

# Function to start Redis (if available)
start_redis() {
    if command_exists "redis-server"; then
        print_status "Starting Redis server..."
        
        if ! check_port 6379; then
            redis-server --daemonize yes --port 6379
            wait_for_service localhost 6379 "Redis"
        else
            print_status "Redis is already running on port 6379"
        fi
    else
        print_warning "Redis not found, skipping Redis startup"
    fi
}

# Function to start PostgreSQL (if available via Docker)
start_postgresql() {
    if command_exists "docker"; then
        print_status "Starting PostgreSQL via Docker..."
        
        if ! check_port 5432; then
            docker run -d \
                --name day60-postgres \
                -e POSTGRES_PASSWORD=password \
                -e POSTGRES_USER=day60 \
                -e POSTGRES_DB=log_replication \
                -p 5432:5432 \
                postgres:15
            
            wait_for_service localhost 5432 "PostgreSQL"
        else
            print_status "PostgreSQL is already running on port 5432"
        fi
    else
        print_warning "Docker not found, skipping PostgreSQL startup"
    fi
}

# Function to create basic application files if they don't exist
create_basic_app() {
    print_status "Creating basic application structure..."
    
    # Create main application file
    if [ ! -f "src/web/main.py" ]; then
        mkdir -p src/web
        cat > src/web/main.py << 'EOF'
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
import structlog
from datetime import datetime
import uuid

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
    title="Day 60: Multi-Region Log Replication System",
    description="A distributed log replication system for high availability",
    version="1.0.0"
)

# In-memory storage for demo purposes
logs = []
connections = []

@app.get("/")
async def root():
    return {
        "message": "Day 60: Multi-Region Log Replication System",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "log_count": len(logs)
    }

@app.post("/logs")
async def add_log(log_data: dict):
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "region": log_data.get("region", "unknown"),
        "level": log_data.get("level", "info"),
        "message": log_data.get("message", ""),
        "metadata": log_data.get("metadata", {})
    }
    
    logs.append(log_entry)
    
    # Broadcast to all connected WebSocket clients
    await broadcast_log(log_entry)
    
    logger.info("Log entry added", log_id=log_entry["id"], region=log_entry["region"])
    
    return {"status": "success", "log_id": log_entry["id"]}

@app.get("/logs")
async def get_logs(region: str = None, limit: int = 100):
    filtered_logs = logs
    
    if region:
        filtered_logs = [log for log in logs if log.get("region") == region]
    
    return {
        "logs": filtered_logs[-limit:],
        "total": len(filtered_logs),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    
    logger.info("WebSocket client connected", client_count=len(connections))
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)
        logger.info("WebSocket client disconnected", client_count=len(connections))

async def broadcast_log(log_entry: dict):
    if connections:
        message = json.dumps({
            "type": "log_entry",
            "data": log_entry
        })
        
        for connection in connections:
            try:
                await connection.send_text(message)
            except:
                connections.remove(connection)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
        print_success "Created main application file"
    fi
    
    # Create configuration file
    if [ ! -f "config/config.json" ]; then
        mkdir -p config
        cat > config/config.json << 'EOF'
{
    "regions": {
        "us-east-1": {
            "name": "US East (N. Virginia)",
            "endpoint": "http://localhost:8000",
            "replication_factor": 3
        },
        "us-west-2": {
            "name": "US West (Oregon)",
            "endpoint": "http://localhost:8001",
            "replication_factor": 3
        },
        "eu-west-1": {
            "name": "Europe (Ireland)",
            "endpoint": "http://localhost:8002",
            "replication_factor": 3
        }
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0
    },
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "log_replication",
        "user": "day60",
        "password": "password"
    },
    "replication": {
        "sync_interval": 5,
        "max_retries": 3,
        "timeout": 30
    }
}
EOF
        print_success "Created configuration file"
    fi
    
    # Create demo script
    if [ ! -f "scripts/demo.py" ]; then
        mkdir -p scripts
        cat > scripts/demo.py << 'EOF'
#!/usr/bin/env python3
"""
Day 60: Multi-Region Log Replication System Demo
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime

class LogReplicationDemo:
    def __init__(self):
        self.regions = [
            {"name": "us-east-1", "url": "http://localhost:8000"},
            {"name": "us-west-2", "url": "http://localhost:8001"},
            {"name": "eu-west-1", "url": "http://localhost:8002"}
        ]
        self.session = None
    
    async def start(self):
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Multi-Region Log Replication Demo")
        print("=" * 50)
        
        # Check system health
        await self.check_health()
        
        # Generate sample logs
        await self.generate_logs()
        
        # Demonstrate replication
        await self.demonstrate_replication()
        
        await self.session.close()
    
    async def check_health(self):
        print("📊 Checking system health...")
        
        for region in self.regions:
            try:
                async with self.session.get(f"{region['url']}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {region['name']}: {data['status']} ({data['log_count']} logs)")
                    else:
                        print(f"❌ {region['name']}: Unhealthy")
            except Exception as e:
                print(f"❌ {region['name']}: Connection failed - {e}")
    
    async def generate_logs(self):
        print("\n📝 Generating sample logs...")
        
        log_levels = ["info", "warning", "error", "debug"]
        log_messages = [
            "User authentication successful",
            "Database connection established",
            "API request processed",
            "Cache miss occurred",
            "Background job completed",
            "System backup started",
            "Security alert triggered",
            "Performance metric recorded"
        ]
        
        for i in range(10):
            region = random.choice(self.regions)
            log_data = {
                "region": region["name"],
                "level": random.choice(log_levels),
                "message": random.choice(log_messages),
                "metadata": {
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "session_id": f"sess_{random.randint(10000, 99999)}",
                    "request_id": f"req_{random.randint(100000, 999999)}"
                }
            }
            
            try:
                async with self.session.post(f"{region['url']}/logs", json=log_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Log added to {region['name']}: {result['log_id'][:8]}...")
                    else:
                        print(f"❌ Failed to add log to {region['name']}")
            except Exception as e:
                print(f"❌ Error adding log to {region['name']}: {e}")
            
            await asyncio.sleep(0.5)
    
    async def demonstrate_replication(self):
        print("\n🔄 Demonstrating log replication...")
        
        # Show logs from each region
        for region in self.regions:
            try:
                async with self.session.get(f"{region['url']}/logs") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n📋 Logs in {region['name']}:")
                        for log in data['logs'][-3:]:  # Show last 3 logs
                            print(f"  - [{log['level'].upper()}] {log['message']} ({log['region']})")
                    else:
                        print(f"❌ Failed to fetch logs from {region['name']}")
            except Exception as e:
                print(f"❌ Error fetching logs from {region['name']}: {e}")
    
    async def cleanup(self):
        print("\n🧹 Cleaning up...")
        if self.session:
            await self.session.close()

async def main():
    demo = LogReplicationDemo()
    try:
        await demo.start()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    finally:
        await demo.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
EOF
        chmod +x scripts/demo.py
        print_success "Created demo script"
    fi
}

# Function to start the application
start_application() {
    print_status "Starting Multi-Region Log Replication System..."
    
    # Start main application
    if ! check_port 8000; then
        print_status "Starting main application on port 8000..."
        python src/web/main.py &
        MAIN_PID=$!
        echo $MAIN_PID > .main.pid
        
        wait_for_service localhost 8000 "Main Application"
    else
        print_status "Main application is already running on port 8000"
    fi
    
    # Start additional region instances (if needed)
    for port in 8001 8002; do
        if ! check_port $port; then
            print_status "Starting region instance on port $port..."
            PORT=$port python src/web/main.py &
            echo $! > .region_$port.pid
            wait_for_service localhost $port "Region Instance ($port)"
        else
            print_status "Region instance is already running on port $port"
        fi
    done
    
    # Start dashboard
    if ! check_port 8080; then
        print_status "Starting dashboard on port 8080..."
        DASHBOARD_PORT=8080 python src/web/dashboard.py &
        echo $! > .dashboard.pid
        wait_for_service localhost 8080 "Dashboard"
    else
        print_status "Dashboard is already running on port 8080"
    fi
}

# Function to show usage instructions
show_instructions() {
    echo
    echo "🎉 Multi-Region Log Replication System is ready!"
    echo "================================================"
    echo
    echo "📋 Available endpoints:"
    echo "  • Dashboard:    http://localhost:8080"
    echo "  • Main API:     http://localhost:8000"
    echo "  • Region 1:     http://localhost:8001"
    echo "  • Region 2:     http://localhost:8002"
    echo "  • Health Check: http://localhost:8000/health"
    echo "  • API Docs:     http://localhost:8000/docs"
    echo
    echo "🚀 Quick Start:"
    echo "  1. View API documentation: open http://localhost:8000/docs"
    echo "  2. Run demo:              python scripts/demo.py"
    echo "  3. Check health:          curl http://localhost:8000/health"
    echo "  4. Add a log:             curl -X POST http://localhost:8000/logs \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"region\":\"us-east-1\",\"level\":\"info\",\"message\":\"Hello World\"}'"
    echo
    echo "📊 Monitoring:"
    echo "  • View logs:              curl http://localhost:8000/logs"
    echo "  • WebSocket connection:   ws://localhost:8000/ws"
    echo
    echo "🛑 To stop the system:"
    echo "  ./stop.sh"
    echo
}

# Main execution
main() {
    echo "🌍 Day 60: Multi-Region Log Replication System"
    echo "=============================================="
    echo
    
    # Verify system requirements
    verify_system
    
    # Create directories
    create_directories
    
    # Setup virtual environment
    setup_venv
    
    # Run tests
    run_tests
    
    # Start Redis
    start_redis
    
    # Start PostgreSQL
    start_postgresql
    
    # Create basic application files
    create_basic_app
    
    # Start application
    start_application
    
    # Show instructions
    show_instructions
}

# Run main function
main "$@" 