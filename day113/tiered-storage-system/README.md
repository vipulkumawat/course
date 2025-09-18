# Tiered Storage System for Distributed Log Processing

## Overview
This system implements intelligent tiered storage for log data, automatically moving logs between storage tiers based on age, access patterns, and cost optimization.

## Features
- **4-Tier Storage Architecture**: Hot, Warm, Cold, Archive
- **Automatic Data Migration**: Policy-driven tier transitions
- **Cost Optimization**: 60-80% storage cost reduction
- **Real-time Dashboard**: Monitor tier utilization and migrations
- **High Performance**: Optimized query routing and caching

## Quick Start

### 1. Build System
```bash
./build.sh
```

### 2. Start Services
```bash
./start.sh
```

### 3. Access Dashboard
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 4. Run Tests
```bash
./test.sh
```

### 5. Stop Services
```bash
./stop.sh
```

## Architecture

### Storage Tiers
- **Hot (SSD)**: 0-7 days, <10ms latency, $200/TB/month
- **Warm (Standard)**: 7-30 days, 50-200ms latency, $50/TB/month
- **Cold (HDD)**: 30-365 days, 1-5s latency, $10/TB/month
- **Archive (Tape)**: 365+ days, 1-5min latency, $1/TB/month

### Migration Policies
- Age-based transitions with configurable thresholds
- Access pattern analysis for intelligent placement
- Priority-based retention for critical data
- Automated background migration processes

## API Endpoints

### Store Log Entry
```bash
curl -X POST http://localhost:8000/api/logs \
  -H "Content-Type: application/json" \
  -d '{"message":"Test log","level":"INFO","service":"api"}'
```

### Retrieve Log Entry
```bash
curl http://localhost:8000/api/logs/{entry_id}
```

### Search Logs
```bash
curl "http://localhost:8000/api/search?q=error&tier=hot"
```

### Get Statistics
```bash
curl http://localhost:8000/api/stats
```

### Trigger Migration
```bash
curl -X POST http://localhost:8000/api/auto-migrate
```

## Docker Deployment

```bash
docker-compose up --build
```

## Configuration

Edit `backend/config/settings.py` to customize:
- Migration thresholds (days)
- Storage paths
- Cost parameters
- Performance settings

## Testing

Run comprehensive test suite:
```bash
./test.sh
```

## Monitoring

The dashboard provides:
- Real-time tier utilization
- Cost analysis and savings
- Migration statistics
- Query performance metrics
- System health indicators

## Performance

Expected metrics:
- **Hot tier**: <10ms query response
- **Migration throughput**: 1000+ entries/minute
- **Cost reduction**: 60-80% over single-tier storage
- **Query cache hit rate**: >80%

## Troubleshooting

1. **Backend not starting**: Check Python version (3.11+ required)
2. **Frontend build issues**: Ensure Node.js 18+ installed
3. **Port conflicts**: Modify ports in start.sh if needed
4. **Permission errors**: Ensure data directories are writable

## Integration

This system integrates with:
- Day 112: Enterprise authentication (LDAP/AD)
- Day 114: Data lifecycle policies (upcoming)
- Distributed log processing pipeline

## License

MIT License - see LICENSE file for details.
