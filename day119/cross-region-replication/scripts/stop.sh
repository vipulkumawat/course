#!/bin/bash

echo "🛑 Stopping Cross-Region Replication System..."

# Kill any running processes
pkill -f "main.py" || true
pkill -f "uvicorn" || true

echo "✅ System stopped"
