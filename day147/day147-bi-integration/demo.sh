#!/bin/bash
set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 Running BI Integration Demo..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found! Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ API server is not running! Please run start.sh first."
    exit 1
fi

# Wait for API to be ready
echo "Waiting for API server..."
sleep 3

# Get authentication token
echo -e "\n1️⃣ Authenticating as Tableau user..."
TOKEN=$(curl -s -X POST http://localhost:8000/oauth/token \
  -d "username=tableau&password=tableau_secret&grant_type=password" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✓ Token obtained: ${TOKEN:0:20}..."

# Get metrics schema
echo -e "\n2️⃣ Fetching available metrics schema..."
curl -s http://localhost:8000/api/v1/metrics/schema \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30

# Query time series data
echo -e "\n3️⃣ Querying time series metrics..."
START=$(date -u -d '1 day ago' '+%Y-%m-%dT%H:%M:%SZ')
END=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

curl -s -X POST http://localhost:8000/api/v1/metrics/timeseries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"measurement\": \"http_requests\",
    \"time_range\": {\"start\": \"$START\", \"end\": \"$END\"},
    \"aggregation_window\": \"1h\",
    \"page\": 1,
    \"page_size\": 10
  }" | python3 -m json.tool | head -40

echo -e "\n4️⃣ Generating CSV export..."
EXPORT_DATE=$(date -u -d '1 day ago' '+%Y-%m-%d')
curl -s -X POST http://localhost:8000/api/v1/exports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"date\": \"${EXPORT_DATE}T00:00:00Z\", \"format\": \"csv\"}" | \
  python3 -m json.tool

echo -e "\n5️⃣ Fetching export manifest..."
curl -s http://localhost:8000/api/v1/exports/manifest \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n✅ Demo completed successfully!"
echo "📊 Access dashboard: http://localhost:8000"
echo "📖 View API docs: http://localhost:8000/docs"
