# Day 60: Multi-Region Log Replication System - Usage Guide

## 🚀 Quick Start

### Starting the System
```bash
./start.sh
```

### Stopping the System
```bash
./stop.sh
```

## 📋 Detailed Usage

### Start Script (`./start.sh`)

The start script performs the following operations in sequence:

1. **System Verification**
   - Checks Python version and availability
   - Verifies required commands (python3, pip, redis-server, docker)
   - Checks port availability (8000, 8001, 8002, 6379, 5432)

2. **Environment Setup**
   - Creates necessary directories
   - Sets up Python virtual environment
   - Installs dependencies from `requirements.txt`

3. **Testing**
   - Runs any available tests in the `tests/` directory

4. **Service Startup**
   - Starts Redis server (if available)
   - Starts PostgreSQL via Docker (if available)
   - Creates basic application files if they don't exist

5. **Application Launch**
   - Starts main application on port 8000
   - Starts region instances on ports 8001 and 8002
   - Waits for services to be ready

6. **Instructions Display**
   - Shows available endpoints
   - Provides usage examples
   - Displays monitoring commands

### Stop Script (`./stop.sh`)

The stop script provides multiple options for stopping the system:

#### Basic Usage
```bash
./stop.sh                    # Stop all services
./stop.sh --check            # Only check running processes
./stop.sh --help             # Show help message
```

#### Advanced Options
```bash
./stop.sh --clean-logs       # Stop services and remove log files
./stop.sh --clean-data       # Stop services and remove all data files
./stop.sh --clean-logs --clean-data  # Stop and clean everything
```

### What Gets Stopped

1. **Python Applications**
   - Main application (port 8000)
   - Region instances (ports 8001, 8002)
   - Any other Python processes on these ports

2. **Services**
   - Redis server (graceful shutdown)
   - PostgreSQL container (if running via Docker)

3. **Docker Containers**
   - All containers with `day60` prefix
   - PostgreSQL container specifically

4. **Cleanup**
   - Removes PID files
   - Optionally removes log files
   - Optionally removes data files

## 🌐 Available Endpoints

Once the system is running, you can access:

| Endpoint | Description | URL |
|----------|-------------|-----|
| Main API | Primary application | http://localhost:8000 |
| Region 1 | US West instance | http://localhost:8001 |
| Region 2 | EU West instance | http://localhost:8002 |
| Health Check | System health status | http://localhost:8000/health |
| API Documentation | Interactive API docs | http://localhost:8000/docs |
| WebSocket | Real-time log streaming | ws://localhost:8000/ws |

## 🧪 Testing the System

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Add a Log Entry
```bash
curl -X POST http://localhost:8000/logs \
  -H 'Content-Type: application/json' \
  -d '{
    "region": "us-east-1",
    "level": "info",
    "message": "User authentication successful",
    "metadata": {
      "user_id": "user123",
      "session_id": "sess456"
    }
  }'
```

### 3. View Logs
```bash
# All logs
curl http://localhost:8000/logs

# Logs from specific region
curl "http://localhost:8000/logs?region=us-east-1"

# Limited number of logs
curl "http://localhost:8000/logs?limit=10"
```

### 4. Run Demo
```bash
python scripts/demo.py
```

## 📊 Monitoring

### Check Running Processes
```bash
./stop.sh --check
```

### View System Status
```bash
# Check all endpoints
for port in 8000 8001 8002; do
  echo "Port $port:"
  curl -s "http://localhost:$port/health" | jq .
done
```

### Monitor Logs in Real-time
```bash
# Using WebSocket (requires a WebSocket client)
# Or use the demo script for automated testing
python scripts/demo.py
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Stop the system and restart
   ./stop.sh
   ./start.sh
   ```

2. **Redis Not Starting**
   ```bash
   # Install Redis (macOS)
   brew install redis
   
   # Start Redis manually
   redis-server --daemonize yes --port 6379
   ```

3. **Docker Not Available**
   ```bash
   # Install Docker Desktop
   # Or use alternative PostgreSQL setup
   ```

4. **Python Dependencies Issues**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Debug Mode

To see detailed output during startup:
```bash
bash -x ./start.sh
```

To see detailed output during shutdown:
```bash
bash -x ./stop.sh
```

## 📁 File Structure

```
day60-multi-region-replication/
├── start.sh              # Start script
├── stop.sh               # Stop script
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── USAGE.md              # This usage guide
├── config/               # Configuration files
│   └── config.json       # System configuration
├── data/                 # Data storage
│   └── regions/          # Region-specific data
├── logs/                 # Application logs
├── scripts/              # Utility scripts
│   └── demo.py           # Demo script
├── src/                  # Source code
│   └── web/              # Web application
│       └── main.py       # Main FastAPI application
├── tests/                # Test files
└── venv/                 # Python virtual environment
```

## 🚀 Advanced Usage

### Custom Configuration

Edit `config/config.json` to modify:
- Region endpoints
- Database settings
- Replication parameters

### Adding New Regions

1. Update `config/config.json`
2. Add region data directory: `mkdir -p data/regions/new-region`
3. Restart the system: `./stop.sh && ./start.sh`

### Persistent Data

To preserve data between restarts:
```bash
# Stop without cleaning data
./stop.sh

# Start again
./start.sh
```

### Clean Restart

To start fresh:
```bash
# Stop and clean everything
./stop.sh --clean-data --clean-logs

# Start again
./start.sh
```

## 🔒 Security Notes

- The demo system runs on localhost only
- No authentication is implemented for demo purposes
- PostgreSQL password is set to "password" for demo
- Redis runs without authentication for demo
- For production use, implement proper security measures

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify system requirements are met
3. Check logs in the `logs/` directory
4. Run `./stop.sh --check` to see running processes
5. Try a clean restart: `./stop.sh --clean-data && ./start.sh` 