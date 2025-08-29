# Day 100: Automated Scaling System

A comprehensive automated scaling system built with Python and React, featuring Kubernetes integration, monitoring, and intelligent scaling policies.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker and Docker Compose
- Kubernetes cluster (optional, for full functionality)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd day100-automated-scaling
   ```

2. **Run the automated setup**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   This script will:
   - Create a Python virtual environment
   - Install Python dependencies
   - Install React dependencies
   - Build the React application
   - Run tests
   - Start the application

3. **Manual setup (alternative)**
   ```bash
   # Python setup
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # React setup
   cd web
   npm install
   npm run build
   cd ..
   
   # Start application
   python -m src.main
   ```

## 🏗️ Project Structure

```
├── src/                    # Python source code
│   ├── api/               # FastAPI endpoints
│   ├── monitoring/        # System monitoring
│   ├── orchestration/     # Kubernetes orchestration
│   ├── policies/          # Scaling policies
│   └── scaling/           # Scaling logic
├── web/                   # React frontend
│   ├── src/               # React components
│   └── public/            # Static assets
├── tests/                 # Test suite
├── config/                # Configuration files
├── docker/                # Docker configurations
└── scripts/               # Utility scripts
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

## 🐳 Docker

Build and run with Docker:
```bash
docker-compose up --build
```

## 📊 Features

- **Real-time Monitoring**: System metrics and performance tracking
- **Intelligent Scaling**: AI-powered scaling decisions
- **Kubernetes Integration**: Native K8s orchestration
- **Policy Engine**: Configurable scaling policies
- **Web Dashboard**: Modern React-based UI
- **API**: RESTful API for integration

## 🔧 Configuration

Configuration files are located in the `config/` directory. Modify these files to customize:
- Scaling policies
- Monitoring thresholds
- Kubernetes settings
- API endpoints

## 📝 Development

### Adding Dependencies
- **Python**: Add to `requirements.txt`
- **React**: Add to `web/package.json`

### Code Style
- Python: Follow PEP 8
- React: Use functional components with hooks
- Tests: Maintain >90% coverage

## 🚫 What's Not Committed

The following items are excluded from version control:
- Virtual environments (`venv/`)
- Node modules (`web/node_modules/`)
- Build artifacts (`web/build/`)
- Cache files (`.pytest_cache/`, `__pycache__/`)
- Package lock files (`package-lock.json`)

## 📞 Support

For issues and questions, please check the test suite and documentation first.
