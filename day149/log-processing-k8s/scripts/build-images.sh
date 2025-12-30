#!/bin/bash

echo "🏗️  Building Docker images..."

# Build storage image
docker build -t log-processing-storage:latest -f docker/Dockerfile.storage .

# Build query image
docker build -t log-processing-query:latest -f docker/Dockerfile.query .

# Build collector image
docker build -t log-processing-collector:latest -f docker/Dockerfile.collector .

# Build dashboard image
docker build -t log-processing-dashboard:latest -f docker/Dockerfile.dashboard .

echo "✅ All images built successfully"
