#!/bin/bash
echo "Stopping SLA Monitoring System..."
pkill -f "python -m src.main" || true
redis-cli shutdown || true
echo "✅ Stopped"
