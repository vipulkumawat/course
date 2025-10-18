#!/bin/bash

source venv/bin/activate

echo "🌍 Starting Cross-Region Replication System..."

# Set Python path
export PYTHONPATH="$(pwd)/backend/src:$PYTHONPATH"

# Start the application
cd backend/src
python main.py
