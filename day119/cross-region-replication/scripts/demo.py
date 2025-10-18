#!/usr/bin/env python3
"""
Demo script for cross-region replication system
"""
import asyncio
import aiohttp
import json
import time
import random

async def run_demo():
    """Run comprehensive demo of the system"""
    print("🎭 Cross-Region Replication System Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with aiohttp.ClientSession() as session:
        # Test system health
        print("1. Testing system health...")
        try:
            async with session.get(f"{base_url}/health/comprehensive") as response:
                if response.status == 200:
                    health = await response.json()
                    print(f"   ✅ System Status: {health.get('overall_status', 'unknown')}")
                    print(f"   📊 Active Regions: {len(health.get('regions', {}).get('regions', {}))}")
                else:
                    print("   ❌ Health check failed")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        await asyncio.sleep(1)
        
        # Test region status
        print("\n2. Checking region status...")
        try:
            async with session.get(f"{base_url}/regions") as response:
                if response.status == 200:
                    regions = await response.json()
                    print(f"   🌍 Total Regions: {regions.get('total_regions', 0)}")
                    print(f"   ✅ Healthy Regions: {regions.get('healthy_regions', 0)}")
                    print(f"   🎯 Primary Region: {regions.get('primary_region', 'N/A')}")
                    
                    for region_id, region_data in regions.get('regions', {}).items():
                        status_emoji = "✅" if region_data['status'] == 'healthy' else "⚠️" if region_data['status'] == 'degraded' else "❌"
                        print(f"   {status_emoji} {region_id}: {region_data['status']} ({region_data['latency_ms']}ms)")
        except Exception as e:
            print(f"   ❌ Region check error: {e}")
            
        await asyncio.sleep(1)
        
        # Submit test logs
        print("\n3. Submitting test log data...")
        services = ['web-server', 'api-gateway', 'database', 'auth-service']
        levels = ['info', 'warning', 'error']
        locations = ['us', 'eu', 'asia']
        
        for i in range(10):
            log_data = {
                "message": f"Demo log entry #{i+1} - {random.choice(['User login', 'API request', 'Database query', 'Cache miss'])}",
                "level": random.choice(levels),
                "service": random.choice(services),
                "metadata": {
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "request_id": f"req_{random.randint(10000, 99999)}"
                }
            }
            
            client_info = {
                "location": random.choice(locations),
                "client_id": f"client_{i+1}"
            }
            
            try:
                async with session.post(
                    f"{base_url}/logs/submit", 
                    json=log_data,
                    params=client_info
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        target_region = result.get('routing_result', {}).get('target_region', 'unknown')
                        print(f"   📝 Log {i+1}: {log_data['level']} → {target_region}")
                    else:
                        print(f"   ❌ Log {i+1}: Failed to submit")
            except Exception as e:
                print(f"   ❌ Log {i+1}: Error - {e}")
                
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(2)
        
        # Check replication metrics
        print("\n4. Checking replication metrics...")
        try:
            async with session.get(f"{base_url}/replication/metrics") as response:
                if response.status == 200:
                    metrics = await response.json()
                    print(f"   📊 Replication Metrics:")
                    for region_id, metric in metrics.items():
                        status = metric.get('status', 'unknown')
                        lag = metric.get('lag_seconds', 0)
                        bytes_replicated = metric.get('bytes_replicated', 0)
                        print(f"   🔄 {region_id}: {status} (lag: {lag:.1f}s, bytes: {bytes_replicated})")
        except Exception as e:
            print(f"   ❌ Metrics check error: {e}")
        
        # Simulate failover
        print("\n5. Simulating regional failover...")
        try:
            # Get current primary region
            async with session.get(f"{base_url}/regions") as response:
                if response.status == 200:
                    regions = await response.json()
                    primary_region = regions.get('primary_region')
                    
                    if primary_region:
                        print(f"   🚨 Triggering failover for: {primary_region}")
                        
                        async with session.post(f"{base_url}/failover/{primary_region}") as failover_response:
                            if failover_response.status == 200:
                                result = await failover_response.json()
                                print(f"   ✅ Failover result: {result.get('status', 'unknown')}")
                                
                                # Wait and check new primary
                                await asyncio.sleep(3)
                                
                                async with session.get(f"{base_url}/regions") as new_response:
                                    if new_response.status == 200:
                                        new_regions = await new_response.json()
                                        new_primary = new_regions.get('primary_region')
                                        print(f"   🎯 New primary region: {new_primary}")
                            else:
                                print("   ❌ Failover failed")
        except Exception as e:
            print(f"   ❌ Failover test error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed!")
        print("🌐 Open http://localhost:8000 to view the dashboard")
        print("📊 WebSocket updates available at ws://localhost:8000/ws")

if __name__ == "__main__":
    asyncio.run(run_demo())
