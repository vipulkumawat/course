#!/bin/bash

echo "Stopping DR System..."

# Kill backend
pkill -f "uvicorn src.api.main:app"

# Kill frontend
pkill -f "react-scripts start"

# Deactivate virtual environment
deactivate 2>/dev/null || true

echo "✅ All services stopped"
