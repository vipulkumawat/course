# Blue/Green Deployment System

A production-ready blue/green deployment system for zero-downtime upgrades of distributed log processing applications.

## Features

- **Zero-downtime deployments** with instant traffic switching
- **Comprehensive health validation** before traffic switch
- **Automatic rollback** on deployment failures
- **Real-time monitoring dashboard** with React frontend
- **RESTful API** for deployment automation
- **Docker containerization** for environment isolation
- **WebSocket updates** for real-time status monitoring

## Quick Start

```bash
# Start the complete system
./start.sh

# Run demonstration
./demo.sh

# Stop the system
./stop.sh
```

## Architecture

- **Deployment Controller**: Orchestrates blue/green deployments
- **Traffic Router**: nginx-based load balancer with dynamic configuration
- **Health Checker**: Multi-dimensional health validation
- **Environment Manager**: Docker-based environment isolation
- **Dashboard**: React-based real-time monitoring interface

## API Endpoints

- `GET /api/v1/status` - Current deployment status
- `POST /api/v1/deploy` - Trigger new deployment
- `GET /api/v1/environments` - Environment health status
- `GET /api/v1/history` - Deployment history
- `POST /api/v1/rollback` - Emergency rollback

## Access Points

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **Blue Environment**: http://localhost:8001
- **Green Environment**: http://localhost:8002
- **Load Balancer**: http://localhost:80

## Testing

```bash
# Unit tests
python -m pytest backend/tests/ -v

# Integration tests
python backend/tests/integration_test.py

# Load testing
./demo.sh
```

## Production Deployment

The system uses Docker Compose for orchestration and can be easily deployed to production environments with proper configuration management and monitoring integration.
