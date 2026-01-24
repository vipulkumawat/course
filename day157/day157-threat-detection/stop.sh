#!/bin/bash

echo "🛑 Stopping Threat Detection System..."

# Kill processes
pkill -f "python -m src.main" || true
pkill -f "python -m src.data_generator" || true

# Deactivate virtual environment
deactivate 2>/dev/null || true

echo "✅ Stopped"
