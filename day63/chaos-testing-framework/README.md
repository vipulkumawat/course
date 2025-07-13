# Chaos Testing Framework for Distributed Log Processing

## Overview

This framework implements comprehensive chaos engineering tools for testing the resilience of distributed log processing systems. It includes failure injection, real-time monitoring, and automated recovery validation.

## Features

### 🌪️ Chaos Scenarios
- **Network Partition**: Simulate network failures between services
- **Resource Exhaustion**: CPU, memory, and disk pressure testing
- **Component Failure**: Service crash and hang simulation
- **Latency Injection**: Network latency testing
- **Packet Loss**: Network reliability testing

### 📊 Real-time Monitoring
- System metrics (CPU, memory, disk, network)
- Service health monitoring
- Custom application metrics
- Alert thresholds and notifications

### 🔍 Recovery Validation
- Automated recovery verification
- Service availability testing
- Data consistency checks
- Performance baseline validation

### 🎯 Safety Controls
- Blast radius limitations
- Concurrent scenario limits
- Severity level controls
- Emergency stop functionality

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (optional)
- Node.js 18+ (for frontend)

### Installation
```bash
# Run the setup script
chmod +x setup.sh
./setup.sh
```

### Running the Application

#### Option 1: Interactive Demo
```bash
cd chaos-testing-framework
./setup.sh
# Choose option 1 for interactive demo
```

#### Option 2: Docker Deployment
```bash
cd chaos-testing-framework/docker
docker-compose up --build
```

#### Option 3: Manual Setup
```bash
cd chaos-testing-framework

# Start backend
source venv/bin/activate
PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m src.web.main

# Start frontend (in another terminal)
cd frontend
npm start
```

## Usage

### Web Dashboard
Access the web dashboard at `http://localhost:3000`

#### Creating Chaos Scenarios
1. Select a scenario type from the dropdown
2. Choose a target service
3. Configure parameters and severity
4. Click "Start Chaos Scenario"

#### Monitoring
- Real-time metrics are displayed in the dashboard
- Service health indicators show current status
- Alerts are triggered when thresholds are exceeded

#### Recovery Validation
- Automatic recovery validation after scenarios
- Manual validation triggers available
- Comprehensive recovery reports

### API Usage
The REST API is available at `http://localhost:8000`

#### Key Endpoints
- `GET /health` - Health check
- `GET /api/chaos/scenarios` - List active scenarios
- `POST /api/chaos/scenarios` - Create new scenario
- `POST /api/chaos/scenarios/{id}/stop` - Stop scenario
- `POST /api/chaos/emergency-stop` - Emergency stop all
- `GET /api/monitoring/metrics` - Current metrics
- `POST /api/recovery/validate/{id}` - Validate recovery

### CLI Usage
```bash
# Run tests
python -m pytest tests/

# Start API server
python -m src.web.main

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('config/chaos_config.yaml')))"
```

## Configuration

### Main Configuration (`config/chaos_config.yaml`)
```yaml
chaos_testing:
  default_duration: 300  # seconds
  safety_timeout: 600
  blast_radius_limit: 0.3
  
  scenarios:
    network_partition:
      enabled: true
      severity_levels: [1, 2, 3, 4, 5]
    
    resource_exhaustion:
      enabled: true
      memory_pressure: [50, 70, 90]
      cpu_throttle: [50, 70, 90]
    
    component_failure:
      enabled: true
      target_services: ["log-collector", "message-queue", "log-processor"]
      failure_types: ["crash", "hang", "slow_response"]

monitoring:
  metrics_interval: 5
  health_check_timeout: 10
  critical_metrics:
    - "log_processing_rate"
    - "message_queue_depth"
    - "system_memory_usage"
    - "network_latency"

recovery:
  auto_recovery_enabled: true
  max_recovery_attempts: 3
  recovery_validation_steps:
    - "service_health_check"
    - "data_consistency_check"
    - "performance_baseline_check"
```

## Architecture

### Backend Components
- **Failure Injector** (`src/chaos/failure_injector.py`)
- **System Monitor** (`src/monitoring/system_monitor.py`)
- **Recovery Validator** (`src/recovery/recovery_validator.py`)
- **Web API** (`src/web/main.py`)

### Frontend Components
- **Control Panel** (`ChaosControlPanel.js`)
- **Metrics Dashboard** (`MetricsDashboard.js`)
- **Scenario Management** (`ScenarioList.js`)
- **Recovery Status** (`RecoveryStatus.js`)

### Docker Services
- **chaos-testing-api**: Main API server
- **chaos-testing-frontend**: React dashboard
- **redis**: Metrics storage
- **Target services**: Log collector, message queue, processor

## Safety Features

### Blast Radius Control
- Maximum 30% of system affected by default
- Configurable per scenario type
- Automatic enforcement

### Concurrent Scenario Limits
- Maximum 3 concurrent scenarios
- Prevents system overload
- Queue management for additional scenarios

### Emergency Recovery
- Immediate stop of all scenarios
- Automatic cleanup of injected failures
- System state restoration

## Testing

### Unit Tests
```bash
python -m pytest tests/unit/ -v
```

### Integration Tests
```bash
python -m pytest tests/integration/ -v
```

### Chaos Tests
```bash
python -m pytest tests/chaos/ -v
```

### End-to-End Testing
```bash
python -m pytest tests/ -v --tb=short
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill processes on required ports
lsof -ti:8000 | xargs kill -9  # API port
lsof -ti:3000 | xargs kill -9  # Frontend port
```

#### Docker Issues
```bash
# Reset Docker environment
docker-compose down -v
docker system prune -f
docker-compose up --build
```

#### Permission Errors
```bash
# Fix permissions
sudo chown -R $USER:$USER .
chmod +x setup.sh
```

### Logs
- Application logs: `logs/chaos_testing.log`
- Docker logs: `docker-compose logs`
- Frontend logs: Browser console

## Development

### Adding New Scenarios
1. Extend `FailureType` enum
2. Add injection method in `FailureInjector`
3. Add recovery method
4. Update configuration schema
5. Add frontend template

### Custom Metrics
1. Extend `SystemMonitor` class
2. Add metric collection method
3. Update alert thresholds
4. Add dashboard visualization

### API Extensions
1. Add endpoints in `main.py`
2. Update frontend services
3. Add tests
4. Update documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Open an issue with detailed reproduction steps
