#!/bin/bash

echo "🔍 Checking Docker installation..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo ""
    echo "📦 To install Docker:"
    echo "   macOS: Download from https://www.docker.com/products/docker-desktop"
    echo "   Linux: sudo apt-get install docker.io docker-compose"
    echo "   Windows: Download Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    echo ""
    echo "🚀 Please start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo ""
    echo "📦 To install Docker Compose:"
    echo "   macOS: Usually comes with Docker Desktop"
    echo "   Linux: sudo apt-get install docker-compose"
    echo "   Or install via pip: pip install docker-compose"
    exit 1
fi

echo "✅ Docker is installed and running"
echo "✅ Docker Compose is available"
echo ""
echo "🚀 You can now run: ./start.sh" 