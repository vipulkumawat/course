#!/bin/bash

echo "🛑 Stopping Security Compliance Reporting System..."

# Kill API process
pkill -f "python src/api/main.py"

# Deactivate virtual environment
deactivate 2>/dev/null

echo "✅ System stopped"
