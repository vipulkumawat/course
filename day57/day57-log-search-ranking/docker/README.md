# Docker Setup for Day 57: Log Search with Ranking System

This directory contains Docker configuration files for running the log search ranking system in containers.

## Files

- `Dockerfile.backend` - Docker image for the Python FastAPI backend
- `Dockerfile.frontend` - Docker image for the React frontend
- `docker-compose.yml` - Orchestration file for both services

## Quick Start

1. **Check Docker installation:**
   ```bash
   ./check-docker.sh
   ```

2. **Start the application:**
   ```bash
   ./start.sh
   ```

3. **Stop the application:**
   ```bash
   ./stop.sh
   ```

## Services

### Backend (Port 8000)
- **Image:** Python 3.11 with FastAPI
- **Health Check:** `GET /health`
- **API Documentation:** http://localhost:8000/docs

### Frontend (Port 3000)
- **Image:** Node.js 18 with React
- **Build:** Production build served with `serve`
- **Health Check:** `GET /`

## Docker Commands

### Build images only:
```bash
docker-compose -f docker/docker-compose.yml build
```

### Start services:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### View logs:
```bash
docker-compose -f docker/docker-compose.yml logs -f
```

### Stop services:
```bash
docker-compose -f docker/docker-compose.yml down
```

### Rebuild and restart:
```bash
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build --no-cache
docker-compose -f docker/docker-compose.yml up -d
```

## Volumes

The following directories are mounted as volumes:
- `../data` → `/app/data` (backend)
- `../logs` → `/app/logs` (backend)

## Environment Variables

### Backend
- `PYTHONPATH=/app`
- `PYTHONUNBUFFERED=1`

### Frontend
- `REACT_APP_API_URL=http://localhost:8000`

## Troubleshooting

### Port conflicts
If ports 8000 or 3000 are already in use, modify the `docker-compose.yml` file to use different ports.

### Build issues
If you encounter build issues:
1. Clean Docker cache: `docker system prune -a`
2. Rebuild without cache: `docker-compose -f docker/docker-compose.yml build --no-cache`

### Health check failures
The services may take a few minutes to start up completely. If health checks fail initially, wait a bit and try again.

## Development

For development, you can still run the services locally without Docker:
- Backend: `cd backend && source venv/bin/activate && python src/main.py`
- Frontend: `cd frontend && npm start` 