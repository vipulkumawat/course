#!/usr/bin/env python3

"""
APM Integration Demo Script
Generates sample logs and metrics to demonstrate the system
"""

import asyncio
import json
import random
import time
from datetime import datetime
import aiohttp

async def generate_sample_logs():
    """Generate sample log entries with various levels and scenarios"""
    
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
    
    async with aiohttp.ClientSession() as session:
        for i in range(50):
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
                async with session.post('http://localhost:8000/logs', json=log_entry) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Log processed: {level} - {message[:30]}... (Enhancement: {result['enhancement_level']})")
                    else:
                        print(f"❌ Failed to process log: {response.status}")
            except Exception as e:
                print(f"❌ Error sending log: {e}")
            
            # Random delay between logs
            await asyncio.sleep(random.uniform(0.5, 2.0))

async def monitor_system():
    """Monitor system metrics and display current status"""
    async with aiohttp.ClientSession() as session:
        for i in range(20):  # Monitor for ~2 minutes
            try:
                async with session.get('http://localhost:8000/metrics/current') as response:
                    if response.status == 200:
                        metrics = await response.json()
                        print(f"📊 System Status - CPU: {metrics['system'].get('cpu', 0):.1f}%, "
                              f"Memory: {metrics['system'].get('memory', 0):.1f}%, "
                              f"Requests: {metrics['application']['request_count']}")
                    else:
                        print(f"❌ Failed to get metrics: {response.status}")
            except Exception as e:
                print(f"❌ Error getting metrics: {e}")
            
            await asyncio.sleep(5)

async def main():
    """Run the complete demo"""
    print("🎬 Starting APM Integration Demo")
    print("=" * 40)
    print()
    print("This demo will:")
    print("1. Generate sample log entries with different levels")
    print("2. Show real-time correlation with system metrics")
    print("3. Demonstrate alert generation")
    print("4. Display enriched logs with performance context")
    print()
    print("👀 Watch the dashboard at: http://localhost:3000")
    print("🔍 API docs at: http://localhost:8000/docs")
    print()
    
    # Wait for user to be ready
    input("Press Enter to start the demo...")
    
    # Run log generation and monitoring concurrently
    await asyncio.gather(
        generate_sample_logs(),
        monitor_system()
    )
    
    print()
    print("✅ Demo completed!")
    print("🌐 Check the dashboard to see enriched logs and performance correlation")

if __name__ == "__main__":
    asyncio.run(main())
