#!/bin/bash

echo "🛑 Stopping Automated Scaling System..."

# Kill any running Python processes for this project
pkill -f "src.main"
pkill -f "uvicorn"

echo "✅ System stopped"
