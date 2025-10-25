#!/bin/bash

echo "🛑 Stopping Data Sovereignty Compliance System"

# Kill API process
pkill -f "python src/api/main.py" || true

echo "✅ System stopped"
