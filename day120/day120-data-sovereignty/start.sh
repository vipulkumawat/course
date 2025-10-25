#!/bin/bash
set -e

echo "🚀 Starting Data Sovereignty Compliance System"

# Activate virtual environment
source venv/bin/activate

# Start API in background
echo "🌐 Starting API server..."
python src/api/main.py &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
sleep 3

# Run demo
echo "🎬 Running demonstration..."
python scripts/demo.py

# Start web dashboard
echo "🌐 Starting web dashboard..."
cd web
npm start &
WEB_PID=$!
cd ..

# Keep API running
echo ""
echo "✅ System is running!"
echo "📊 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🖥️  Dashboard: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop..."

wait $API_PID $WEB_PID
