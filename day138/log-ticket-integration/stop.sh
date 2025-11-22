#!/bin/bash

echo "🛑 Stopping JIRA/ServiceNow Ticket Integration System"
echo "=================================================="

# Stop Redis container if running
docker stop redis-ticket-system > /dev/null 2>&1 || true
docker rm redis-ticket-system > /dev/null 2>&1 || true

# Kill any running Python processes
pkill -f "python -m src.main" || true

echo "✅ System stopped successfully!"
