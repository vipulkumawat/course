# Day 159: IOC Scanner System

Production-ready Indicators of Compromise (IOC) scanning system for distributed log processing.

## Features

- Real-time IOC pattern matching (1000+ logs/second)
- Multi-source threat intelligence integration
- Bloom filter optimized lookups
- Severity-based alert generation
- Live threat detection dashboard

## Quick Start

### Option 1: Automated Setup
```bash
chmod +x setup.sh && ./setup.sh
```

### Option 2: Manual Setup
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start services
./start.sh
```

### Option 3: Docker
```bash
docker-compose up --build
```

## Access Points

- **API Server**: http://localhost:8000
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Testing

```bash
# Unit tests
python -m pytest tests/ -v

# Load test
python tests/load_test.py

# Live demonstration
python scripts/demo.py
```

## Architecture

- **Scanner Engine**: Concurrent IOC matching with thread pool
- **IOC Database**: Redis-backed with Bloom filter optimization
- **Feed Manager**: Automatic threat intelligence updates
- **Alert System**: Severity-scored security events
- **Dashboard**: Real-time React visualization

## Performance

- Throughput: 1000+ logs/second
- Latency: <50ms per log
- Cache hit rate: >90%
- Memory: <500MB

## Project Structure

```
day159_ioc_scanner/
├── src/
│   ├── scanner/       # Core scanning engine
│   ├── feeds/         # Threat feed management
│   ├── matcher/       # IOC matching logic
│   └── api/           # REST API
├── tests/             # Test suite
├── web/               # React dashboard
├── config/            # Configuration
└── docker/            # Docker files
```

## License

MIT License - Educational use only
