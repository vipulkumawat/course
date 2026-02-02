# Service Dependency Mapper

A real-time service dependency discovery and visualization tool that analyzes log files to build dependency graphs, detect issues, and provide impact analysis.

## Features

- 🔍 **Real-time Dependency Discovery**: Automatically parses log files to discover service dependencies
- 📊 **Interactive Visualization**: Beautiful D3.js-powered graph visualization of service dependencies
- ⚠️ **Issue Detection**: Automatically detects circular dependencies and single points of failure
- 🎯 **Impact Analysis**: Simulate service failures to understand cascading impacts
- 🔗 **Critical Path Analysis**: Identify the most critical dependency paths in your system
- 📈 **Real-time Updates**: WebSocket-based live updates as new dependencies are discovered

## Architecture

- **Backend**: Python-based WebSocket server that parses logs and maintains dependency graph
- **Frontend**: HTML/CSS/JavaScript dashboard with D3.js visualization
- **Components**:
  - `parser.py`: Parses log entries to extract dependency information
  - `graph.py`: Maintains and analyzes the dependency graph
  - `analyzer.py`: Performs impact analysis and pattern detection
  - `server.py`: WebSocket server for real-time communication

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dependency-mapper
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

1. Start the services:
```bash
bash run_services.sh
```

2. Access the dashboard:
   - From WSL/Linux: `http://localhost:8000`
   - From Windows: `http://localhost:8000` or use the WSL IP address

3. Stop the services:
```bash
./stop.sh
```

### Manual Start

If you prefer to start services manually:

1. Start the WebSocket server:
```bash
cd backend
PYTHONPATH="$(pwd):$PYTHONPATH" python server.py ../logs/sample.log
```

2. In another terminal, start the HTTP server:
```bash
cd frontend
python http_server.py
```

### Docker

Build and run with Docker:

```bash
docker build -t dependency-mapper .
docker run -p 8000:8000 -p 8765:8765 dependency-mapper
```

## Log Format

The tool expects log files with entries that contain dependency information. Example format:

```
2024-01-15 10:30:45 service-a -> service-b latency: 120ms type: http
```

The parser extracts:
- **Caller**: The service making the call
- **Callee**: The service being called
- **Latency**: Response time
- **Type**: Type of dependency (http, database, etc.)
- **Timestamp**: When the dependency occurred

## Dashboard Features

### Dependency Graph
- Interactive visualization of all service dependencies
- Click on nodes to see details
- Real-time updates as new dependencies are discovered

### Statistics
- Total number of services
- Total number of dependencies

### Alerts & Warnings
- **Circular Dependencies**: Detects dependency cycles that could cause issues
- **Single Points of Failure**: Identifies services that many others depend on

### Critical Paths
- Shows the most critical dependency paths based on latency and importance

## API

The WebSocket server accepts the following message types:

- `get_impact`: Simulate failure of a service
  ```json
  {
    "type": "get_impact",
    "service": "service-name"
  }
  ```

- `get_critical_paths`: Get critical dependency paths
  ```json
  {
    "type": "get_critical_paths"
  }
  ```

## Project Structure

```
dependency-mapper/
├── backend/
│   ├── analyzer.py      # Impact analysis and pattern detection
│   ├── graph.py         # Dependency graph management
│   ├── parser.py        # Log file parsing
│   └── server.py        # WebSocket server
├── frontend/
│   ├── app.js           # Frontend JavaScript
│   ├── http_server.py   # HTTP server for dashboard
│   └── index.html       # Dashboard UI
├── logs/
│   └── sample.log       # Sample log file
├── tests/
│   ├── test_analyzer.py
│   ├── test_graph.py
│   └── test_parser.py
├── Dockerfile
├── requirements.txt
├── run_services.sh      # Start all services
├── start.sh            # Alternative start script
├── stop.sh             # Stop all services
└── ACCESS.md           # Access instructions
```

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## Troubleshooting

### Connection Issues

If you can't access the dashboard from Windows:

1. Check if services are running:
```bash
netstat -tuln | grep -E ':(8000|8765)'
```

2. Verify Windows Firewall isn't blocking connections

3. Try using the WSL IP address instead of localhost

4. See `ACCESS.md` for detailed troubleshooting steps

### Services Not Starting

- Ensure the virtual environment is activated
- Check that ports 8000 and 8765 are not in use
- Review log files in `logs/` directory

## Development

### Adding New Features

- **Parser**: Extend `parser.py` to support new log formats
- **Graph**: Add new analysis methods in `graph.py`
- **Analyzer**: Implement new detection patterns in `analyzer.py`
- **Frontend**: Modify `app.js` and `index.html` for UI changes

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
