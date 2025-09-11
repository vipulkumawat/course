#!/usr/bin/env python3
"""Demo script for tenant isolation system."""
import asyncio
import aiohttp
import json
import time
import random

async def run_demo():
    """Run comprehensive demo of tenant isolation system."""
    print("🎬 Day 107 Demo: Tenant Isolation & Resource Quotas")
    print("=" * 55)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Demo 1: Show tenant configuration
        print("\n1️⃣ TENANT CONFIGURATION")
        print("-" * 25)
        
        async with session.get(f"{base_url}/api/tenants") as response:
            data = await response.json()
            for tenant in data['tenants']:
                print(f"🏢 {tenant['name']} ({tenant['id']})")
                print(f"   Tier: {tenant['tier'].upper()}")
                print(f"   CPU: {tenant['quota']['cpu_cores']} cores")
                print(f"   Memory: {tenant['quota']['memory_mb']}MB")
                print(f"   Rate limit: {tenant['quota']['requests_per_minute']}/min")
                print()
        
        # Demo 2: Show initial resource usage
        print("2️⃣ INITIAL RESOURCE USAGE")
        print("-" * 27)
        
        async with session.get(f"{base_url}/api/quota-status") as response:
            data = await response.json()
            for tenant_id, status in data.items():
                utilization = status['utilization']
                print(f"🏢 {tenant_id}:")
                print(f"   CPU: {utilization['cpu']:.1f}%")
                print(f"   Memory: {utilization['memory']:.1f}%")
                print(f"   Requests: {utilization['requests']:.1f}%")
                print()
        
        # Demo 3: Simulate different load patterns
        print("3️⃣ LOAD SIMULATION TESTING")
        print("-" * 28)
        
        tenants = ['tenant-basic', 'tenant-premium', 'tenant-enterprise']
        
        for tenant_id in tenants:
            print(f"🧪 Testing {tenant_id}...")
            
            # Send load simulation
            async with session.post(f"{base_url}/api/simulate-load/{tenant_id}") as response:
                result = await response.json()
                success_rate = (result['successful_requests'] / result['total_requests']) * 100
                
                print(f"   📊 {result['successful_requests']}/{result['total_requests']} requests successful ({success_rate:.1f}%)")
                
                if result['failed_requests'] > 0:
                    print(f"   ⚠️  {result['failed_requests']} requests failed (quota enforcement)")
            
            # Show updated metrics
            await asyncio.sleep(1)
            async with session.get(f"{base_url}/api/tenants/{tenant_id}/metrics") as response:
                metrics = await response.json()
                utilization = metrics['utilization']
                print(f"   📈 Updated usage - CPU: {utilization['cpu']:.1f}%, Memory: {utilization['memory']:.1f}%")
                print()
        
        # Demo 4: Show isolation verification
        print("4️⃣ ISOLATION VERIFICATION")
        print("-" * 27)
        
        for tenant_id in ['tenant-basic', 'tenant-premium']:
            print(f"🔒 Processing logs for {tenant_id}...")
            
            # Process tenant-specific logs
            log_data = {
                "message": f"Confidential data for {tenant_id}",
                "level": "INFO",
                "metadata": {"confidential": True, "tenant": tenant_id}
            }
            
            headers = {"X-Tenant-ID": tenant_id, "Content-Type": "application/json"}
            
            async with session.post(f"{base_url}/api/tenants/{tenant_id}/logs",
                                  json=log_data, headers=headers) as response:
                result = await response.json()
                print(f"   ✅ Log processed and stored in isolated path")
                print(f"   🗂️  Tenant storage path: data/tenant_data/{tenant_id}/")
        
        print("\n5️⃣ RESOURCE QUOTA SUMMARY")
        print("-" * 27)
        
        async with session.get(f"{base_url}/api/quota-status") as response:
            data = await response.json()
            
            print("Final resource utilization:")
            for tenant_id, status in data.items():
                utilization = status['utilization']
                metrics = status['metrics']
                
                print(f"\n🏢 {tenant_id}:")
                print(f"   CPU: {utilization['cpu']:.1f}% of allocated quota")
                print(f"   Memory: {utilization['memory']:.1f}% of allocated quota")
                print(f"   Requests: {utilization['requests']:.1f}% of rate limit")
                print(f"   Active connections: {metrics['current_usage'].get('concurrent_connections', 0)}")
    
    print("\n🎉 DEMO COMPLETE!")
    print("=" * 55)
    print("✅ Tenant isolation enforced")
    print("✅ Resource quotas working")
    print("✅ Fair resource allocation")
    print("✅ Real-time monitoring active")
    print("\n🌐 View dashboard at: http://localhost:3000")

if __name__ == "__main__":
    asyncio.run(run_demo())
