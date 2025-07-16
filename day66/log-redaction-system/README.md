# Log Redaction System

A comprehensive log redaction system with FastAPI backend and React frontend.

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Setup

1. **Install Python dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start the system:**
   ```bash
   ./start.sh
   ```

3. **Stop the system:**
   ```bash
   ./stop.sh
   ```

4. **Check status:**
   ```bash
   ./status.sh
   ```

## Scripts Overview

### `start.sh`
- Starts the FastAPI backend on port 8000
- Starts the React frontend on port 3000
- Creates necessary directories (logs, pids)
- Automatically creates basic FastAPI app if none exists
- Automatically creates basic React app if none exists
- Handles dependency installation
- Provides colored output and status messages

### `stop.sh`
- Gracefully stops both backend and frontend services
- Uses PID files for precise process management
- Falls back to port-based process termination
- Cleans up PID files
- Provides colored output and status messages

### `status.sh`
- Checks if services are running
- Verifies port availability
- Tests service health endpoints
- Displays service URLs and quick commands

## Services

### Backend API (Port 8000)
- FastAPI-based REST API
- Health check endpoint: `/health`
- CORS enabled for frontend communication
- Auto-reload enabled for development

### Frontend (Port 3000)
- React-based web interface
- Connects to backend API
- Real-time status monitoring
- Modern UI with responsive design

## Directory Structure

```
log-redaction-system/
├── start.sh          # Start script
├── stop.sh           # Stop script
├── status.sh         # Status script
├── requirements.txt  # Python dependencies
├── src/             # Backend source code
├── frontend/        # Frontend source code
├── logs/            # Service logs (created by start.sh)
├── pids/            # Process ID files (created by start.sh)
└── venv/            # Python virtual environment
```

## Logs

Service logs are stored in the `logs/` directory:
- `backend.log` - FastAPI backend logs
- `frontend.log` - React frontend logs

## Troubleshooting

### Port Already in Use
If you see "Port X is already in use" error:
```bash
# Find processes using the port
lsof -i :8000  # For backend
lsof -i :3000  # For frontend

# Kill the process
kill -9 <PID>
```

### Virtual Environment Issues
If the virtual environment is not found:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Dependencies
If frontend dependencies are missing:
```bash
cd frontend
npm install
```

## Development

### Backend Development
- The backend uses FastAPI with auto-reload
- Changes to Python files will automatically restart the server
- API documentation available at: http://localhost:8000/docs

### Frontend Development
- The frontend uses React with hot reload
- Changes to JavaScript/JSX files will automatically refresh the browser
- Development server runs on: http://localhost:3000

## Production Deployment

For production deployment, consider:
- Using a production WSGI server (Gunicorn)
- Building the frontend for production (`npm run build`)
- Setting up proper environment variables
- Using a reverse proxy (Nginx)
- Implementing proper logging and monitoring 