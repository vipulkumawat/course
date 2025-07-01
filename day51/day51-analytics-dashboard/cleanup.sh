#!/bin/bash
set -e

# 1. Kill running FastAPI/uvicorn processes
PIDS=$(ps aux | grep -E 'src/main.py|uvicorn' | grep -v grep | awk '{print $2}')
if [ ! -z "$PIDS" ]; then
  echo "Killing app processes: $PIDS"
  kill $PIDS || true
fi

# 2. Remove Python cache and temp files
find . -type d -name '__pycache__' -exec rm -rf {} +
rm -rf .pytest_cache .mypy_cache .coverage

# 3. Remove Docker containers/images related to the project
DOCKER_CONTAINERS=$(docker ps -a --filter "name=analytics" --format "{{.ID}}")
if [ ! -z "$DOCKER_CONTAINERS" ]; then
  echo "Removing Docker containers: $DOCKER_CONTAINERS"
  docker rm -f $DOCKER_CONTAINERS || true
fi
DOCKER_IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep analytics | awk '{print $2}')
if [ ! -z "$DOCKER_IMAGES" ]; then
  echo "Removing Docker images: $DOCKER_IMAGES"
  docker rmi -f $DOCKER_IMAGES || true
fi

echo "✅ Cleanup complete." 