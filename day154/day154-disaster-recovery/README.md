# Day 154: Disaster Recovery Procedures

Production-ready disaster recovery system with automated failover, RTO/RPO measurement, and chaos engineering.

## Quick Start

### Option 1: Automated Setup
```bash
./start.sh
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start backend
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd web && npm install && npm start
```

### Option 3: Docker
```bash
docker-compose up --build
```

## Features

- ✅ Automated failover with RTO/RPO tracking
- ✅ Multi-region replication
- ✅ Chaos engineering tests
- ✅ Real-time monitoring dashboard
- ✅ Comprehensive metrics and reporting

## API Endpoints

- GET `/api/status` - System status
- GET `/api/metrics` - DR and replication metrics
- POST `/api/trigger-failover` - Manual failover
- POST `/api/chaos/run/{scenario}` - Run chaos test
- GET `/api/failover-history` - Failover events

## Dashboard

Access at: http://localhost:3000

## Running Demo

```bash
python scripts/demo.py
```

## Tests

```bash
# All tests
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v
```

## Configuration

Edit `config/dr_config.yaml` to customize:
- RTO/RPO targets
- Region configuration
- Replication settings
- Health check intervals

## Stopping

```bash
./stop.sh
```

Or press Ctrl+C in the terminal where services are running.
