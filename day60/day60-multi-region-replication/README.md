# Day 60: Multi-Region Log Replication System

## Overview
This project implements a distributed log replication system that can replicate logs across multiple regions for high availability and disaster recovery.

## Project Structure
```
day60-multi-region-replication/
├── config/           # Configuration files
├── data/            # Data storage
├── docker/          # Docker configuration
├── logs/            # Application logs
├── scripts/         # Utility scripts
├── src/             # Source code
│   ├── conflict/    # Conflict resolution logic
│   ├── monitoring/  # System monitoring
│   ├── regions/     # Region-specific code
│   ├── replication/ # Replication logic
│   └── web/         # Web interface
├── tests/           # Test files
├── venv/            # Python virtual environment
└── requirements.txt  # Python dependencies
```

## Setup
The project has been set up with the following dependencies:
- FastAPI for web API
- Uvicorn for ASGI server
- AsyncPG for PostgreSQL async operations
- Redis for caching and coordination
- WebSockets for real-time communication
- Pytest for testing
- Structlog for structured logging
- Matplotlib for data visualization
- NumPy for numerical operations

## Installation
1. Virtual environment is already created and activated
2. Dependencies are installed in `venv/`
3. All packages are compatible with Python 3.13

## Next Steps
To complete the implementation, you'll need to:

1. **Implement the replication logic** in `src/replication/`
2. **Create region-specific handlers** in `src/regions/`
3. **Build conflict resolution** in `src/conflict/`
4. **Add monitoring** in `src/monitoring/`
5. **Create web interface** in `src/web/`
6. **Write tests** in `tests/`
7. **Configure Docker** in `docker/`
8. **Add configuration files** in `config/`

## 🚀 Quick Start

### Starting the System
```bash
./start.sh
```

### Stopping the System
```bash
./stop.sh
```

## 📋 Available Endpoints

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

### Health Check
```bash
curl http://localhost:8000/health
```

### Add a Log Entry
```bash
curl -X POST http://localhost:8000/logs \
  -H 'Content-Type: application/json' \
  -d '{
    "region": "us-east-1",
    "level": "info",
    "message": "User authentication successful"
  }'
```

### Run Demo
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

## 📖 Detailed Usage

For comprehensive usage instructions, see [USAGE.md](USAGE.md).

## 🛠️ Manual Operation

If you prefer to run components manually:

### Running the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Run the FastAPI application
uvicorn src.web.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run tests
pytest tests/
```

## 🐳 Docker Support
Docker configuration files will be added to the `docker/` directory for containerized deployment. 