#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting JIRA/ServiceNow Ticket Integration System"
echo "==================================================="

# Check if Redis is running
check_redis() {
    if command -v redis-cli > /dev/null 2>&1; then
        redis-cli ping > /dev/null 2>&1
    elif command -v docker > /dev/null 2>&1; then
        docker exec redis-ticket-system redis-cli ping > /dev/null 2>&1
    else
        return 1
    fi
}

if ! check_redis; then
    echo "⚠️  Redis not running. Starting Redis with Docker..."
    if command -v docker > /dev/null 2>&1; then
        # Check if container exists
        if docker ps -a --format '{{.Names}}' | grep -q "^redis-ticket-system$"; then
            echo "🔄 Starting existing Redis container..."
            docker start redis-ticket-system > /dev/null 2>&1 || true
        else
            echo "🐳 Creating new Redis container..."
            docker run -d --name redis-ticket-system -p 6379:6379 redis:7-alpine > /dev/null 2>&1 || true
        fi
        echo "⏳ Waiting for Redis to be ready..."
        sleep 5
        # Verify Redis is actually responding
        for i in {1..10}; do
            if check_redis; then
                echo "✅ Redis is ready!"
                break
            fi
            if [ $i -eq 10 ]; then
                echo "⚠️  Redis container started but not responding. Continuing anyway..."
            else
                sleep 1
            fi
        done
    else
        echo "❌ Docker not found. Please start Redis manually."
        exit 1
    fi
else
    echo "✅ Redis is already running"
fi

# Check if virtual environment exists
if [ ! -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Check if Python module exists
if [ ! -f "$SCRIPT_DIR/src/main.py" ]; then
    echo "❌ Main application not found at $SCRIPT_DIR/src/main.py"
    exit 1
fi

# Start the application
echo "🎯 Starting ticket integration service on http://localhost:8000"
echo "📊 Dashboard will be available at http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop..."

cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
python -m src.main