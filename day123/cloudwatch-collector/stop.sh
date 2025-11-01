#!/bin/bash

echo "🛑 Stopping CloudWatch Collector..."

# Find and kill Python processes
pkill -f "python src/main.py" || true

echo "✅ Collector stopped"
