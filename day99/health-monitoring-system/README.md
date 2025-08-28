# Health Monitoring System

A comprehensive health monitoring system that tracks system metrics, generates alerts, and provides real-time monitoring capabilities.

## Features

- Real-time system metrics monitoring
- Automated alert generation
- RESTful API for data access
- Mock services for testing
- Docker support
- Frontend dashboard

## Project Structure

```
health-monitoring-system/
├── src/                    # Source code
├── tests/                  # Test files
├── frontend/               # Frontend application
├── config/                 # Configuration files
├── docker/                 # Docker configuration
├── scripts/                # Utility scripts
├── data/                   # Data storage (gitignored)
├── requirements.txt        # Python dependencies
├── start.sh               # Start all services
├── stop.sh                # Stop all services
├── test.sh                # Run tests
└── demo.sh                # Demo script
```

## Prerequisites

- Python 3.8+
- Docker (optional)
- Node.js (for frontend)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd health-monitoring-system
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the system**
   ```bash
   ./start.sh
   ```

4. **Run tests**
   ```bash
   ./test.sh
   ```

5. **Stop the system**
   ```bash
   ./stop.sh
   ```

## Development

### Running Tests
```bash
./test.sh
```

### Running Demo
```bash
./demo.sh
```

### Code Structure
- `src/` - Main application code
- `tests/` - Test suite
- `frontend/` - Web interface
- `config/` - Configuration files

## Configuration

Configuration files are located in the `config/` directory. Modify these files to customize the system behavior.

## API Documentation

The system provides a RESTful API for accessing health metrics and alerts. API documentation is available when the service is running.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license information here]

## Support

For support and questions, please [create an issue](link-to-issues) or contact the development team.
