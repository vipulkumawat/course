#!/bin/bash

echo "🛑 Stopping GDPR Compliance System..."

# Kill any Python processes running on port 8000 or 8001
echo "🔍 Stopping Python servers..."
pkill -f "uvicorn.*8000" || true
pkill -f "uvicorn.*8001" || true

# Stop Docker containers if running
echo "🐳 Stopping Docker containers..."
docker-compose down 2>/dev/null || true

# Clean up test database
echo "🧹 Cleaning up test database..."
rm -f gdpr_test.db

echo "✅ GDPR Compliance System stopped!" 