#!/bin/bash
set -e

echo "🚀 Starting NLP Query System..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start API server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
