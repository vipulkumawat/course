#!/bin/bash
# Start Log Ingestion Service
# Usage: ./start_ingestion.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if manager script exists
MANAGER_SCRIPT="$SCRIPT_DIR/src/multi_project_manager.py"
if [ ! -f "$MANAGER_SCRIPT" ]; then
    echo "❌ Manager script not found at $MANAGER_SCRIPT"
    exit 1
fi

echo "🚀 Starting GCP Log Ingestion Service..."
echo "   Press Ctrl+C to stop"
echo ""

cd "$SCRIPT_DIR"
python -m src.multi_project_manager

