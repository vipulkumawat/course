#!/bin/bash
set -e

# 1. Setup venv if not present
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Run all tests
pytest tests --maxfail=1 --disable-warnings

# 4. Start the FastAPI app in the background
APP_PID=""
python3 src/main.py &
APP_PID=$!

# 5. Wait for the app to start
sleep 5

# 6. Check health endpoint
HEALTH=$(curl -s http://localhost:8000/health || true)
if [[ "$HEALTH" == *"healthy"* ]]; then
  echo "✅ App health check passed."
else
  echo "❌ App health check failed."
  kill $APP_PID
  exit 1
fi

# 7. Stop the app
kill $APP_PID
wait $APP_PID 2>/dev/null || true

echo "✅ Build, test, and verify completed successfully." 