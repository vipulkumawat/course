#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎬 Running CloudWatch Collector Demo..."
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "❌ Error: curl not found. Please install curl"
    exit 1
fi

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install python3"
    exit 1
fi

# Check if services are running
HEALTH_URL="http://localhost:5000/health"
if ! curl -s "$HEALTH_URL" > /dev/null 2>&1; then
    echo "❌ Collector not running at $HEALTH_URL"
    echo "   Start it with: $SCRIPT_DIR/start.sh or docker-compose up"
    exit 1
fi

echo "✅ Collector is running"
echo ""

# Show stats
STATS_URL="http://localhost:5000/api/stats"
echo "📊 Current Statistics from $STATS_URL:"
if curl -s "$STATS_URL" | python3 -m json.tool 2>/dev/null; then
    echo ""
else
    echo "⚠️  Failed to retrieve stats"
fi

# Show metrics
METRICS_URL="http://localhost:8000/metrics"
echo "📈 Prometheus Metrics from $METRICS_URL:"
if curl -s "$METRICS_URL" 2>/dev/null | grep "cloudwatch_logs"; then
    echo ""
else
    echo "⚠️  No cloudwatch_logs metrics found"
fi

echo "🌐 Dashboard: http://localhost:5000"
echo "📊 Metrics: http://localhost:8000/metrics"
echo ""
echo "Demo complete! Press Ctrl+C to stop monitoring."
