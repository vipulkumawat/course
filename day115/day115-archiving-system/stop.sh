#!/bin/bash

echo "🛑 Stopping Historical Data Archiving System..."

# Kill any running processes
pkill -f "python src/main.py" || true

echo "✅ System stopped"
