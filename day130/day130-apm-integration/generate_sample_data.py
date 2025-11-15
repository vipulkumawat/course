#!/usr/bin/env python3
"""
Quick script to generate sample logs for testing the APM system
"""

import json
import random
import time
import urllib.request
import urllib.parse

def generate_sample_logs(count=20):
    """Generate sample log entries"""
    services = ['api', 'database', 'auth', 'payment', 'notification']
    levels = ['INFO', 'WARNING', 'ERROR']
    messages = {
        'INFO': [
            'Request processed successfully',
            'User logged in',
            'Cache hit for key',
            'Configuration loaded',
            'Health check passed'
        ],
        'WARNING': [
            'High memory usage detected',
            'Connection pool nearly full',
            'Slow query detected',
            'Rate limit approaching',
            'Disk space low'
        ],
        'ERROR': [
            'Database connection failed',
            'Authentication failed',
            'Payment processing error',
            'Service unavailable',
            'Timeout occurred'
        ]
    }
    
    for i in range(count):
        service = random.choice(services)
        level = random.choice(levels)
        message = random.choice(messages[level])
        
        log_entry = {
            'timestamp': time.time(),
            'level': level,
            'service': service,
            'message': message,
            'request_id': f'req_{random.randint(1000, 9999)}',
            'user_id': random.randint(1, 1000)
        }
        
        try:
            data = json.dumps(log_entry).encode('utf-8')
            req = urllib.request.Request(
                'http://localhost:8000/logs',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"✅ Log {i+1}/{count}: {level} - {message[:40]}... (Enhancement: {result['enhancement_level']})")
                else:
                    print(f"❌ Failed to process log: {response.status}")
        except Exception as e:
            print(f"❌ Error sending log: {e}")
        
        # Small delay between logs
        time.sleep(0.5)
    
    print(f"\n✅ Generated {count} sample logs!")
    print("📝 Check the Log Viewer at http://localhost:3000")
    print("🚨 Check the Alerts panel if any thresholds were exceeded")

if __name__ == "__main__":
    generate_sample_logs(30)

