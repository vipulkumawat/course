# Day 57: Full-Text Search with Ranking Implementation

A distributed log processing system with intelligent search capabilities and relevance ranking.

## Features

- **Intelligent Log Search**: TF-IDF based relevance scoring
- **Multi-factor Ranking**: Contextual relevance adjustments
- **Real-time Search Suggestions**: Auto-completion and query suggestions
- **Modern React Interface**: Material-UI based search interface
- **FastAPI Backend**: High-performance Python backend
- **Comprehensive Testing**: Unit, integration, and performance tests

## Project Structure

```
day57-log-search-ranking/
├── backend/                 # Python FastAPI backend
│   ├── src/
│   │   ├── main.py         # Application entry point
│   │   ├── search/         # Search engine components
│   │   ├── ranking/        # Ranking algorithms
│   │   ├── models/         # Data models
│   │   └── utils/          # Utility functions
│   ├── tests/              # Test suite
│   └── venv/               # Python virtual environment
├── frontend/               # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── utils/          # Frontend utilities
│   └── public/             # Static assets
├── data/                   # Sample data and logs
├── logs/                   # Application logs
├── scripts/                # Build and deployment scripts
└── docs/                   # Documentation
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)

### Installation

1. **Clone and setup the project:**
   ```bash
   ./setup.sh
   ```

2. **Start the system:**
   ```bash
   ./start.sh
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (if setup.sh fails)

If the automatic setup fails, you can manually set up the project:

#### Backend Setup
```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run build
```

## Usage

### Search Interface

1. **Basic Search**: Enter search terms in the search box
2. **Contextual Search**: Use search mode and user focus options
3. **Sample Queries**: Click on suggested queries to try them
4. **Results**: View ranked results with relevance scores and explanations

### API Endpoints

- `POST /api/search` - Search logs with ranking
- `GET /api/search/suggestions` - Get search suggestions
- `GET /api/search/stats` - Get system statistics

### Sample Queries

- `authentication error`
- `payment timeout`
- `database connection`
- `user session`
- `api response time`
- `memory usage high`

## Architecture

### Backend Components

- **Search Engine**: TF-IDF based search with query expansion
- **Ranking Engine**: Multi-factor relevance scoring
- **Query Parser**: Intelligent query parsing and expansion
- **Models**: Pydantic data models for type safety

### Frontend Components

- **SearchInterface**: Main search component with Material-UI
- **SearchService**: API communication layer
- **Results Display**: Ranked results with relevance explanations

## Development

### Running Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest tests/

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Backend
cd backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
serve -s build
```

## Key Features Implemented

✅ **TF-IDF based relevance scoring**
✅ **Multi-factor ranking algorithm**
✅ **Contextual relevance adjustments**
✅ **Real-time search suggestions**
✅ **Intelligent query parsing and expansion**
✅ **Performance monitoring and statistics**
✅ **React-based search interface**
✅ **Comprehensive test suite**

## Next Steps

- Day 58: Build RESTful API for programmatic access
- Integration with existing log processing pipeline
- Performance optimization and caching strategies
- Advanced ranking algorithms and machine learning

## Troubleshooting

### Common Issues

1. **Frontend build fails**: Check Node.js version and dependencies
2. **Backend startup fails**: Ensure Python 3.11+ and virtual environment
3. **API connection errors**: Verify backend is running on port 8000

### Logs

- Backend logs: `logs/backend.log`
- Frontend logs: Browser developer console
- System logs: `logs/system.log`

## License

This project is part of the Distributed Systems course curriculum. 