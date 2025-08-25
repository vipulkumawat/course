# Day 97: Saved Searches and Alerts System

A full-stack web application for managing saved searches and setting up alerts.

## Project Structure

```
├── backend/           # FastAPI backend
├── frontend/          # React frontend
├── docker/            # Docker configuration
├── scripts/           # Utility scripts
├── tests/             # Test files
├── start.sh           # Start all services
├── stop.sh            # Stop all services
├── cleanup.sh         # Clean up for check-in
└── README.md          # This file
```

## Quick Start

1. **Start the system:**
   ```bash
   ./start.sh
   ```

2. **Stop the system:**
   ```bash
   ./stop.sh
   ```

3. **Clean up for check-in:**
   ```bash
   ./cleanup.sh
   ```

## Services

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Cleanup for Check-in

Before committing your code, run the cleanup script to remove:

- Python virtual environment (`venv/`)
- Node.js dependencies (`frontend/node_modules/`)
- Database files (`*.db`)
- Build artifacts and cache files
- Temporary files and logs
- PID files

**Note**: In WSL environments, some Windows-specific Node.js binaries may not be removable due to I/O errors. This is normal and won't affect the cleanup process.

## Restoring After Cleanup

After running cleanup, you can restore the project by running:

```bash
./start.sh
```

This will:
1. Create a new Python virtual environment
2. Install Python dependencies
3. Initialize the database
4. Install Node.js dependencies
5. Start both frontend and backend services

## Development

- **Backend**: FastAPI with SQLite database
- **Frontend**: React with Vite and Tailwind CSS
- **Database**: SQLite (automatically created on startup)
