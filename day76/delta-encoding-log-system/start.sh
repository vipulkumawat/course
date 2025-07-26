#!/bin/bash

echo "🚀 Starting Delta Encoding Log System"
echo "====================================="

# Activate virtual environment
source venv/bin/activate

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create data directories
mkdir -p data/compressed_logs data/backups logs

# Start the application
echo "📊 Starting dashboard on http://localhost:6000"
python -m src.main &
APP_PID=$!

# Wait for startup
sleep 5

echo "✅ System started successfully!"
echo "📊 Dashboard: http://localhost:6000"
echo "🔧 API docs: http://localhost:6000/docs"
echo "📈 Statistics: http://localhost:6000/api/stats"
echo ""
echo "📝 To stop the system, run: ./stop.sh"

# Save PID for cleanup
echo $APP_PID > .app.pid

wait $APP_PID
