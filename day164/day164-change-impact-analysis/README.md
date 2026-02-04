# Day 164: Change Impact Analysis System

Predict the impact of changes across your distributed log processing system.

## Quick Start

```bash
./start.sh    # Start all services
./demo.sh     # Run demonstration
./stop.sh     # Stop all services
```

## Docker Deployment

```bash
docker-compose up --build
```

## Manual Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
python src/api_server.py
```

## Access

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000

## Testing

```bash
# Run tests
python -m pytest tests/ -v

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/services

# Analyze change
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"change_type": "api_modification", "target_service": "log-enrichment", "change_description": "Add field"}'
```
