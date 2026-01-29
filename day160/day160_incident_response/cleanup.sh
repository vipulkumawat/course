#!/bin/bash

# Cleanup script for Day 160 Incident Response System
# Stops containers and removes unused Docker resources

set -e

echo "🧹 Starting cleanup process..."
echo "================================"

# Stop all running containers
echo "📦 Stopping all Docker containers..."
docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"

# Remove all containers
echo "🗑️  Removing all Docker containers..."
docker rm $(docker ps -aq) 2>/dev/null || echo "No containers to remove"

# Remove all unused images
echo "🖼️  Removing unused Docker images..."
docker image prune -a -f 2>/dev/null || echo "No unused images to remove"

# Remove all unused volumes
echo "💾 Removing unused Docker volumes..."
docker volume prune -f 2>/dev/null || echo "No unused volumes to remove"

# Remove all unused networks
echo "🌐 Removing unused Docker networks..."
docker network prune -f 2>/dev/null || echo "No unused networks to remove"

# Remove all unused build cache
echo "🔨 Removing unused Docker build cache..."
docker builder prune -a -f 2>/dev/null || echo "No build cache to remove"

# System prune (removes everything unused)
echo "🧽 Running Docker system prune..."
docker system prune -a -f --volumes 2>/dev/null || echo "Docker system prune completed"

echo ""
echo "✅ Docker cleanup completed!"
echo ""
echo "📊 Docker disk usage:"
docker system df 2>/dev/null || echo "Docker not available"
