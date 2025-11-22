# JIRA/ServiceNow Ticket Integration System

Day 138 of the 254-Day Hands-On System Design Series

## Overview

Automatic ticket creation system that analyzes log events and creates appropriate tickets in JIRA or ServiceNow based on configurable rules.

## Features

- ✅ Automatic event classification and ticket routing
- ✅ JIRA and ServiceNow API integration
- ✅ Intelligent deduplication using event fingerprints
- ✅ Template-based ticket creation
- ✅ Real-time monitoring dashboard
- ✅ Background event processing with Redis
- ✅ Comprehensive test suite

## Quick Start

```bash
# Build and test
./build.sh

# Start system
./start.sh

# Run demo
./demo.sh
```

## Architecture

The system processes log events through several stages:
1. Event classification and priority assignment
2. Fingerprint generation for deduplication
3. Template-based ticket content generation
4. API integration with target systems
5. Ticket lifecycle management

## API Endpoints

- `GET /` - System information
- `GET /health` - Health check
- `POST /api/events/submit` - Submit log event
- `GET /api/dashboard/stats` - Dashboard statistics
- `POST /api/tickets/create` - Create ticket manually

## Configuration

Edit `.env` file to configure:
- JIRA credentials and project
- ServiceNow instance and credentials
- Redis connection settings
- Processing parameters

## Testing

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests  
python -m pytest tests/integration/ -v

# All tests with coverage
./test.sh
```

## Development

The system is built with:
- **Backend**: FastAPI + Python 3.11
- **Frontend**: React + Tailwind CSS
- **Queue**: Redis
- **APIs**: JIRA REST API v3, ServiceNow Table API

## Production Deployment

```bash
# Docker deployment
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f ticket-service
```
