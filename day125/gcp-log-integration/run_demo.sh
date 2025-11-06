#!/bin/bash
# Run Demo Script to Generate Test Metrics
# Usage: ./run_demo.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if demo script exists
DEMO_SCRIPT="$SCRIPT_DIR/src/demo_ingestion.py"
if [ ! -f "$DEMO_SCRIPT" ]; then
    echo "❌ Demo script not found at $DEMO_SCRIPT"
    exit 1
fi

echo "🎬 Running Demo: Simulating Log Ingestion..."
echo ""

cd "$SCRIPT_DIR"
python -m src.demo_ingestion

