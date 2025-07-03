# Distributed Search System

A distributed search system with consistent hashing, multiple index nodes, and a web dashboard.

## 🏗️ Project Structure

```
distributed-search/
├── src/
│   ├── coordinator/          # Coordinator service
│   │   ├── hash_ring.py     # Consistent hash ring implementation
│   │   └── main.py          # Coordinator API server
│   ├── node/                # Index node services
│   │   ├── index_node.py    # Index node implementation
│   │   └── main.py          # Node server
│   └── storage/             # Storage layer (Redis)
├── web/                     # Web dashboard
│   ├── dashboard.html       # Main dashboard interface
│   └── server.py           # Web server
├── tests/                   # Test files
│   ├── test_basic.py       # Basic hash ring tests
│   └── test_distributed_search.py  # Comprehensive system tests
├── config/                  # Configuration files
│   └── cluster.yaml        # Cluster configuration
├── logs/                    # Log files (auto-created)
├── venv/                    # Virtual environment
├── requirements.txt         # Python dependencies
├── demo_start.sh           # Start all services
├── demo_cleanup.sh         # Stop all services
├── build_instructions.sh   # Build and test instructions
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Start the System
```bash
./demo_start.sh
```

This will start:
- Redis infrastructure
- 4 index nodes (ports 8101-8104)
- Coordinator API (port 8000)
- Web dashboard (port 8080)
- Load test data

### 2. Access the Dashboard
Open your browser and go to: [http://localhost:8080/dashboard.html](http://localhost:8080/dashboard.html)

### 3. Stop the System
```bash
./demo_cleanup.sh
```

## 🔧 Manual Testing

### Search via Coordinator API
```bash
curl -X POST http://localhost:8000/search \
     -H 'Content-Type: application/json' \
     -d '{"terms": ["error"]}'
```

### Check Node Health
```bash
curl http://localhost:8101/health
```

### Get Node Statistics
```bash
curl http://localhost:8101/stats
```

## 🧪 Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_distributed_search.py -v
```

## 📊 System Components

### Index Nodes (ports 8101-8104)
- Handle document indexing and search
- Use Redis for storage
- Implement term-based search with scoring

### Coordinator (port 8000)
- Coordinates searches across all nodes
- Uses consistent hashing for load distribution
- Provides unified API interface

### Web Dashboard (port 8080)
- Real-time system monitoring
- Interactive search interface
- Cluster statistics and health monitoring

## 🔗 API Endpoints

### Coordinator API (port 8000)
- `GET /` - System info
- `GET /health` - Health check
- `POST /search` - Distributed search
- `POST /index` - Index document
- `GET /stats` - Cluster statistics
- `GET /hash-distribution` - Hash ring info

### Index Node API (ports 8101-8104)
- `GET /health` - Node health
- `GET /stats` - Node statistics
- `POST /search` - Local search
- `POST /index` - Index document

## 🛠️ Development

### Prerequisites
- Python 3.11+
- Redis server
- Virtual environment (auto-created)

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📝 Features

- ✅ Consistent hash ring distribution
- ✅ Multi-node index storage
- ✅ Distributed query coordination
- ✅ Fault-tolerant search
- ✅ Real-time web dashboard
- ✅ CORS-enabled APIs
- ✅ Comprehensive test suite
- ✅ Performance monitoring

## 🎯 Use Cases

- Distributed log search
- Multi-tenant search systems
- Scalable document indexing
- High-availability search clusters 