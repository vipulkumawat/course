#!/bin/bash
# Stop script for structured logging helpers

echo "🛑 Stopping Structured Logging Helpers System"
echo "============================================="

# Kill any Python processes on port 8000
PIDS=$(lsof -ti:8000)
if [ ! -z "$PIDS" ]; then
    echo "🔪 Stopping dashboard processes..."
    kill $PIDS
    echo "✅ Dashboard stopped"
else
    echo "ℹ️  No dashboard processes found"
fi

# Kill any remaining demo processes
pkill -f "src/main.py" 2>/dev/null || true

echo "✅ All processes stopped"
