#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Day 153 Infrastructure Monitoring System"
echo "===================================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Check for duplicate processes
check_process() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  $name is already running on port $port"
        return 1
    fi
    return 0
}

# Check for existing processes
if ! check_process 8000 "Log metrics exporter"; then
    echo "   Stopping existing exporter..."
    pkill -f "log_metrics_exporter.py" 2>/dev/null || true
    sleep 2
fi

if ! check_process 5000 "Dashboard"; then
    echo "   Stopping existing dashboard..."
    pkill -f "dashboard.py" 2>/dev/null || true
    sleep 2
fi

# Determine Python command - use system Python with installed packages
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON_CMD="venv/bin/python3"
elif [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
else
    PYTHON_CMD="python"
fi

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Start Docker services
echo "🐳 Starting Docker services (Prometheus, Node Exporter, Grafana)..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
    docker compose up -d
else
    echo "⚠️  Docker not found, skipping Docker services"
fi

echo "⏳ Waiting for services to be ready..."
sleep 15

# Start custom exporter
echo "📊 Starting custom log metrics exporter..."
EXPORTER_SCRIPT="$SCRIPT_DIR/src/exporters/log_metrics_exporter.py"
if [ -f "$EXPORTER_SCRIPT" ]; then
    $PYTHON_CMD "$EXPORTER_SCRIPT" &
    EXPORTER_PID=$!
    echo "   Exporter PID: $EXPORTER_PID"
    echo $EXPORTER_PID > "$SCRIPT_DIR/.exporter.pid"
else
    echo "❌ Exporter script not found at $EXPORTER_SCRIPT"
    EXPORTER_PID=""
fi

# Start correlation engine
echo "🔗 Starting correlation analysis engine..."
CORRELATION_SCRIPT="$SCRIPT_DIR/src/analytics/correlation_engine.py"
if [ -f "$CORRELATION_SCRIPT" ]; then
    $PYTHON_CMD "$CORRELATION_SCRIPT" &
    CORRELATION_PID=$!
    echo "   Correlation PID: $CORRELATION_PID"
    echo $CORRELATION_PID > "$SCRIPT_DIR/.correlation.pid"
else
    echo "⚠️  Correlation engine script not found, skipping"
    CORRELATION_PID=""
fi

# Start dashboard
echo "🌐 Starting web dashboard..."
DASHBOARD_SCRIPT="$SCRIPT_DIR/src/web/dashboard.py"
if [ -f "$DASHBOARD_SCRIPT" ]; then
    $PYTHON_CMD "$DASHBOARD_SCRIPT" &
    DASHBOARD_PID=$!
    echo "   Dashboard PID: $DASHBOARD_PID"
    echo $DASHBOARD_PID > "$SCRIPT_DIR/.dashboard.pid"
else
    echo "❌ Dashboard script not found at $DASHBOARD_SCRIPT"
    DASHBOARD_PID=""
fi

echo ""
echo "✅ All services started!"
echo ""
echo "Access points:"
echo "  - Dashboard:   http://localhost:5000"
echo "  - Prometheus:  http://localhost:9090"
echo "  - Grafana:     http://localhost:3000 (admin/admin)"
echo "  - Node Metrics: http://localhost:9100/metrics"
echo "  - Log Metrics:  http://localhost:8000/metrics"
echo ""
echo "Run './stop.sh' to stop all services"
