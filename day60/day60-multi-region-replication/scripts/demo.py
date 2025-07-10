#!/usr/bin/env python3
"""
Day 60: Multi-Region Log Replication System Demo
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime

class LogReplicationDemo:
    def __init__(self):
        self.regions = [
            {"name": "us-east-1", "url": "http://localhost:8000"},
            {"name": "us-west-2", "url": "http://localhost:8001"},
            {"name": "eu-west-1", "url": "http://localhost:8002"}
        ]
        self.session = None
    
    async def start(self):
        self.session = aiohttp.ClientSession()
        print("🚀 Starting Multi-Region Log Replication Demo")
        print("=" * 50)
        
        # Check system health
        await self.check_health()
        
        # Generate sample logs
        await self.generate_logs()
        
        # Demonstrate replication
        await self.demonstrate_replication()
        
        await self.session.close()
    
    async def check_health(self):
        print("📊 Checking system health...")
        
        for region in self.regions:
            try:
                async with self.session.get(f"{region['url']}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {region['name']}: {data['status']} ({data['log_count']} logs)")
                    else:
                        print(f"❌ {region['name']}: Unhealthy")
            except Exception as e:
                print(f"❌ {region['name']}: Connection failed - {e}")
    
    async def generate_logs(self):
        print("\n📝 Generating sample logs...")
        
        log_levels = ["info", "warning", "error", "debug"]
        log_messages = [
            "User authentication successful",
            "Database connection established",
            "API request processed",
            "Cache miss occurred",
            "Background job completed",
            "System backup started",
            "Security alert triggered",
            "Performance metric recorded"
        ]
        
        for i in range(10):
            region = random.choice(self.regions)
            log_data = {
                "region": region["name"],
                "level": random.choice(log_levels),
                "message": random.choice(log_messages),
                "metadata": {
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "session_id": f"sess_{random.randint(10000, 99999)}",
                    "request_id": f"req_{random.randint(100000, 999999)}"
                }
            }
            
            try:
                async with self.session.post(f"{region['url']}/logs", json=log_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Log added to {region['name']}: {result['log_id'][:8]}...")
                    else:
                        print(f"❌ Failed to add log to {region['name']}")
            except Exception as e:
                print(f"❌ Error adding log to {region['name']}: {e}")
            
            await asyncio.sleep(0.5)
    
    async def demonstrate_replication(self):
        print("\n🔄 Demonstrating log replication...")
        
        # Show logs from each region
        for region in self.regions:
            try:
                async with self.session.get(f"{region['url']}/logs") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n📋 Logs in {region['name']}:")
                        for log in data['logs'][-3:]:  # Show last 3 logs
                            print(f"  - [{log['level'].upper()}] {log['message']} ({log['region']})")
                    else:
                        print(f"❌ Failed to fetch logs from {region['name']}")
            except Exception as e:
                print(f"❌ Error fetching logs from {region['name']}: {e}")
    
    async def cleanup(self):
        print("\n🧹 Cleaning up...")
        if self.session:
            await self.session.close()

async def main():
    demo = LogReplicationDemo()
    try:
        await demo.start()
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    finally:
        await demo.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
