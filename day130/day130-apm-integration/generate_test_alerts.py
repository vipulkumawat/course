#!/usr/bin/env python3
"""
Script to generate test alerts for demonstration purposes
"""

import json
import time
import redis
import random

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Generate some test alerts
alerts = [
    {
        'type': 'CPU_CRITICAL',
        'value': 92.5,
        'threshold': 90.0,
        'correlation_id': f'corr_{int(time.time())}_{random.randint(1000, 9999)}',
        'timestamp': int(time.time())
    },
    {
        'type': 'MEMORY_CRITICAL',
        'value': 87.3,
        'threshold': 85.0,
        'correlation_id': f'corr_{int(time.time())}_{random.randint(1000, 9999)}',
        'timestamp': int(time.time()) - 60  # 1 minute ago
    },
    {
        'type': 'CPU_CRITICAL',
        'value': 91.2,
        'threshold': 90.0,
        'correlation_id': f'corr_{int(time.time())}_{random.randint(1000, 9999)}',
        'timestamp': int(time.time()) - 120  # 2 minutes ago
    },
    {
        'type': 'RESPONSE_TIME_CRITICAL',
        'value': 2150,
        'threshold': 2000,
        'correlation_id': f'corr_{int(time.time())}_{random.randint(1000, 9999)}',
        'timestamp': int(time.time()) - 180  # 3 minutes ago
    },
    {
        'type': 'MEMORY_CRITICAL',
        'value': 88.7,
        'threshold': 85.0,
        'correlation_id': f'corr_{int(time.time())}_{random.randint(1000, 9999)}',
        'timestamp': int(time.time()) - 240  # 4 minutes ago
    }
]

print("🚨 Generating test alerts...")
for i, alert in enumerate(alerts):
    alert_key = f"alerts:{alert['timestamp']}"
    r.set(alert_key, json.dumps(alert), ex=3600)  # 1 hour expiry
    print(f"✅ Alert {i+1}/{len(alerts)}: {alert['type']} - Value: {alert['value']}, Threshold: {alert['threshold']}")

print(f"\n✅ Generated {len(alerts)} test alerts!")
print("📊 Check the Alerts panel at http://localhost:3000")
print("💡 Alerts will expire in 1 hour")

