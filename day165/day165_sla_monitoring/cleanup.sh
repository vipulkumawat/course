#!/bin/bash
set -e

echo "🧹 Starting Docker cleanup process..."
echo "======================================"

# Stop and remove containers from docker-compose
if [ -f "docker-compose.yml" ]; then
    echo "📦 Stopping docker-compose services..."
    docker-compose down -v 2>/dev/null || true
    echo "✅ docker-compose services stopped"
fi

# Stop any running containers related to this project
echo "🛑 Stopping project containers..."
docker ps -a --filter "name=day165" --filter "name=sla-monitor" -q | xargs -r docker stop 2>/dev/null || true
docker ps -a --filter "name=day165" --filter "name=sla-monitor" -q | xargs -r docker rm 2>/dev/null || true
echo "✅ Project containers removed"

# Remove unused Docker resources
echo "🗑️  Removing unused Docker resources..."

# Remove dangling images
echo "  - Removing dangling images..."
docker image prune -f 2>/dev/null || true

# Remove unused containers
echo "  - Removing stopped containers..."
docker container prune -f 2>/dev/null || true

# Remove unused networks
echo "  - Removing unused networks..."
docker network prune -f 2>/dev/null || true

# Remove unused volumes
echo "  - Removing unused volumes..."
docker volume prune -f 2>/dev/null || true

# Remove build cache (optional - uncomment if you want to clear build cache)
# echo "  - Removing build cache..."
# docker builder prune -f 2>/dev/null || true

# Remove images related to this project
echo "🖼️  Removing project images..."
docker images --filter "reference=day165_sla_monitoring*" -q | xargs -r docker rmi -f 2>/dev/null || true
docker images --filter "reference=*sla-monitor*" -q | xargs -r docker rmi -f 2>/dev/null || true
echo "✅ Project images removed"

echo ""
echo "✅ Docker cleanup completed!"
echo "======================================"
echo "Summary:"
echo "  - Stopped and removed containers"
echo "  - Removed unused Docker resources"
echo "  - Removed project-specific images"
echo ""
echo "💡 To see remaining Docker resources:"
echo "   docker ps -a"
echo "   docker images"
echo "   docker volume ls"
