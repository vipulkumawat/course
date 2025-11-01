# Day 123: AWS CloudWatch Log Collector

Production-ready CloudWatch log collector with multi-account support, real-time streaming, and intelligent buffering.

## Features

- ✅ Multi-account AWS log collection
- ✅ Automatic log group discovery
- ✅ Real-time event streaming
- ✅ Intelligent batching and buffering
- ✅ Circuit breaker pattern for resilience
- ✅ Prometheus metrics export
- ✅ Real-time web dashboard
- ✅ Docker deployment

## Quick Start

### Local Development
```bash
# Build and test
./build.sh

# Configure AWS credentials
cp .env.example .env
# Edit .env with your AWS credentials

# Start collector
./start.sh
```

### Docker Deployment
```bash
# Build Docker images
./docker-build.sh

# Start services
docker-compose up -d

# View logs
docker-compose logs -f collector
```

## Configuration

Edit `config/config.yaml` to customize:

- AWS regions and accounts
- Discovery and polling intervals
- Batch sizes and timeouts
- Filter patterns
- Circuit breaker settings

## Monitoring

- **Dashboard**: http://localhost:5000
- **Metrics**: http://localhost:8000/metrics
- **Health**: http://localhost:5000/health

## Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suite
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

## Architecture

See `docs/day123_cloudwatch_integration.md` for detailed architecture documentation.

## License

MIT License - Day 123 of 254-Day System Design Series
