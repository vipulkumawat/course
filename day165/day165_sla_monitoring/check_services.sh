#!/bin/bash
# Script to check for duplicate services

echo "🔍 Checking for running services..."

# Check for Redis
redis_count=$(pgrep -f "redis-server" | wc -l)
if [ $redis_count -gt 0 ]; then
    echo "⚠️  Found $redis_count Redis server process(es)"
    pgrep -f "redis-server" | xargs ps -p 2>/dev/null || true
else
    echo "✅ No Redis server running"
fi

# Check for SLA monitoring system
sla_count=$(pgrep -f "python.*src.main" | wc -l)
if [ $sla_count -gt 0 ]; then
    echo "⚠️  Found $sla_count SLA monitoring process(es)"
    pgrep -f "python.*src.main" | xargs ps -p 2>/dev/null || true
    exit 1
else
    echo "✅ No SLA monitoring system running"
    exit 0
fi
