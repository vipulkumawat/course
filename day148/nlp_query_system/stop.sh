#!/bin/bash

echo "🛑 Stopping NLP Query System..."

# Kill uvicorn processes
pkill -f "uvicorn src.api.app" || true

# Stop Docker containers if running
docker-compose down 2>/dev/null || true

echo "✅ System stopped"
