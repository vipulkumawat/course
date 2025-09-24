#!/bin/bash
set -e

echo "🚀 Starting Historical Data Archiving System..."

# Activate virtual environment
source venv/bin/activate

# Start the application
python src/main.py
