# Day 156: SIEM Implementation

A comprehensive Security Information and Event Management (SIEM) system built with Python, FastAPI, and Redis. This system provides real-time security event correlation, threat detection, and incident management with a modern web dashboard.

## 🛡️ Features

- **Real-time Event Processing**: Ingest and normalize security events from multiple sources
- **Threat Detection**: Automated detection of:
  - Brute force attacks
  - Privilege escalation attempts
  - Anomalous access patterns
  - Data exfiltration attempts
- **Risk Scoring**: Dynamic risk calculation based on event severity and context
- **Incident Management**: Automatic incident creation and correlation
- **Web Dashboard**: Real-time dashboard with live metrics and incident visualization
- **REST API**: Comprehensive API for event ingestion and data retrieval
- **WebSocket Support**: Real-time incident updates via WebSocket connections

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Cleanup](#cleanup)

## 🔧 Prerequisites

- Python 3.11 or higher
- Redis (or Docker for Redis)
- pip (Python package manager)

## 📦 Installation

### Option 1: Manual Installation

1. Clone the repository:
```bash
cd day156_siem_implementation
```

2. Create a virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Start Redis:
```bash
# Using Docker (recommended)
docker run -d --name siem-redis -p 6379:6379 redis:7-alpine

# Or using system Redis
redis-server
```

### Option 2: Using Setup Script

Run the setup script to create the project structure:
```bash
bash setup.sh
cd day156_siem_implementation
```

## 🚀 Quick Start

1. Start the SIEM system:
```bash
./start.sh
```

2. Access the dashboard:
   - Dashboard: http://localhost:8000/dashboard
   - API: http://localhost:8000
   - Health Check: http://localhost:8000/health

3. Generate test events:
```bash
python scripts/generate_test_data.py
```

4. Stop the system:
```bash
./stop.sh
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (or modify the existing one):
```env
REDIS_HOST=localhost
REDIS_PORT=6379
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_PORT=3000
LOG_LEVEL=INFO
```

### SIEM Configuration

Edit `config/siem_config.yaml` to customize:
- Correlation time windows
- Detection rule thresholds
- Risk scoring weights
- Alerting severities

Example configuration:
```yaml
correlation:
  time_window_seconds: 300
  suspicious_threshold: 0.7

detection_rules:
  brute_force:
    enabled: true
    failed_attempts_threshold: 5
    time_window_seconds: 60
```

## 📖 Usage

### Starting the Server

```bash
# Using the start script (recommended)
./start.sh

# Or manually
source venv/bin/activate
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### Ingesting Events

Send security events to the API:

```bash
# Authentication event
curl -X POST http://localhost:8000/api/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "type": "auth",
    "username": "user1",
    "source_ip": "192.168.1.100",
    "success": false,
    "timestamp": 1234567890.0
  }'

# Access event
curl -X POST http://localhost:8000/api/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "type": "access",
    "user": "user1",
    "client_ip": "192.168.1.100",
    "resource_path": "/api/data",
    "action": "read",
    "status_code": 200
  }'
```

### Viewing Incidents

```bash
# Get all incidents
curl http://localhost:8000/api/incidents

# Get statistics
curl http://localhost:8000/api/statistics
```

## 🔌 API Documentation

### Endpoints

#### Health Check
- `GET /` - Root endpoint (redirects to dashboard)
- `GET /health` - Detailed health check with statistics

#### Event Ingestion
- `POST /api/events/ingest` - Ingest a security event
  - Body: JSON event data
  - Returns: Event processing result

#### Incidents
- `GET /api/incidents?limit=50` - Get recent incidents
  - Query params: `limit` (default: 50)

#### Statistics
- `GET /api/statistics` - Get SIEM statistics
  - Returns: Total events, incidents by severity, active incidents

#### Dashboard
- `GET /dashboard` - Serve the web dashboard

#### WebSocket
- `WS /ws/incidents` - Real-time incident updates

### Event Types

The system supports three event types:

1. **Authentication Events** (`type: "auth"`)
   - Fields: `username`, `source_ip`, `success`, `auth_method`, `service`

2. **Access Events** (`type: "access"`)
   - Fields: `user`, `client_ip`, `resource_path`, `action`, `status_code`, `bytes`

3. **Admin Events** (`type: "admin"`)
   - Fields: `user`, `source_ip`, `action`, `command`, `success`

## 📁 Project Structure

```
day156_siem_implementation/
├── src/
│   ├── siem/
│   │   └── engine.py          # Core SIEM engine and correlation logic
│   ├── processors/
│   │   └── normalizer.py      # Event normalization
│   ├── api/
│   │   └── server.py          # FastAPI server
│   └── dashboard/
├── tests/
│   └── test_siem_engine.py    # Unit tests
├── config/
│   └── siem_config.yaml       # SIEM configuration
├── web/
│   └── templates/
│       └── dashboard.html     # Web dashboard
├── scripts/
│   ├── generate_test_data.py # Test event generator
│   └── cleanup.sh            # Cleanup script
├── data/
│   ├── events/               # Event storage
│   ├── incidents/            # Incident storage
│   └── rules/                # Detection rules
├── logs/                     # Application logs
├── docker/                   # Docker files
├── requirements.txt          # Python dependencies
├── start.sh                  # Start script
├── stop.sh                   # Stop script
├── cleanup.sh                # Cleanup script
├── docker-compose.yml        # Docker Compose configuration
└── README.md                 # This file
```

## 🧪 Testing

Run the test suite:
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Data Generation

Generate realistic security events for testing:
```bash
python scripts/generate_test_data.py
```

This will simulate:
- Normal user activity
- Brute force attacks
- Privilege escalation attempts
- Anomalous access patterns

## 🐳 Docker Deployment

### Using Docker Compose

```bash
docker-compose up -d
```

This will start:
- Redis container
- SIEM API server

### Manual Docker Build

```bash
# Build the image
docker build -t siem-app -f docker/Dockerfile .

# Run the container
docker run -d -p 8000:8000 --name siem siem-app
```

## 🧹 Cleanup

Run the cleanup script to remove:
- Python cache files
- Virtual environment
- Docker containers and unused resources
- Temporary files

```bash
./cleanup.sh
```

## 🔍 Detection Rules

### Brute Force Detection
- Detects multiple failed authentication attempts
- Configurable threshold (default: 5 attempts in 60 seconds)
- Escalates to CRITICAL if followed by successful login

### Privilege Escalation Detection
- Monitors for suspicious privilege actions (sudo, su, admin)
- Requires multiple actions within time window
- High severity incident

### Anomalous Access Detection
- Detects access from new/unusual IP addresses
- Flags access to critical resources
- Medium severity incident

## 📊 Dashboard Features

- **Real-time Metrics**: Live updates of events and incidents
- **Statistics Cards**: Total events, incidents by severity
- **Incident List**: Recent security incidents with details
- **WebSocket Updates**: Automatic refresh on new incidents
- **Manual Refresh**: Refresh button to update all metrics

## 🛠️ Development

### Adding New Detection Rules

1. Add rule configuration to `config/siem_config.yaml`
2. Implement detection logic in `src/siem/engine.py`
3. Add tests in `tests/test_siem_engine.py`

### Adding New Event Types

1. Add event type to `EventType` enum in `src/siem/engine.py`
2. Create normalizer method in `src/processors/normalizer.py`
3. Update API endpoint in `src/api/server.py`

## 📝 License

This project is part of a learning course (Day 156).

## 🤝 Contributing

This is a course project. For improvements:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues or questions, please check:
- API health: http://localhost:8000/health
- Server logs: Check `server.log` or console output
- Redis connection: Ensure Redis is running on port 6379

## 🎯 Next Steps

- [ ] Add more detection rules
- [ ] Implement alerting channels (email, webhook)
- [ ] Add data persistence layer
- [ ] Enhance dashboard with charts
- [ ] Add authentication/authorization
- [ ] Implement incident response workflows

---

**Built with**: Python 3.11, FastAPI, Redis, HTML/CSS/JavaScript
