#!/bin/bash
set -e

echo "🐳 Building Docker images..."

# Build image
docker-compose build

echo "✅ Docker build complete!"
echo ""
echo "To start: docker-compose up -d"
