#!/bin/bash
set -e

echo "🐳 Building Day 107 with Docker"
echo "==============================="

# Build and start services
docker-compose build
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health checks
echo "🏥 Performing health checks..."
curl -f http://localhost:8000/health || (echo "❌ Backend health check failed" && exit 1)
curl -f http://localhost:3000 || (echo "❌ Frontend health check failed" && exit 1)

echo "✅ Docker deployment successful!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo ""
echo "Run 'docker-compose logs -f' to view logs"
echo "Run 'docker-compose down' to stop services"
