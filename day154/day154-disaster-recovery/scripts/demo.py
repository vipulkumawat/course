#!/usr/bin/env python3
import asyncio
import requests
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

API_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def demonstrate_dr_system():
    """Demonstrate DR system capabilities"""
    
    print_section("🛡️ Disaster Recovery System Demonstration")
    
    # Wait for API to be ready
    print("Waiting for API to be ready...")
    for _ in range(30):
        try:
            response = requests.get(f"{API_URL}/api/status")
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ API failed to start")
        return
    
    print("✅ API is ready!\n")
    
    # 1. Show initial status
    print_section("1️⃣ Initial System Status")
    response = requests.get(f"{API_URL}/api/status")
    status = response.json()
    print(f"Primary Region: {status['primary_region']}")
    for region, details in status['regions'].items():
        print(f"  {region}: {details['role']} - {details['status']}")
    
    # 2. Show metrics
    print_section("2️⃣ Initial Metrics")
    response = requests.get(f"{API_URL}/api/metrics")
    metrics = response.json()
    dr_metrics = metrics['dr_metrics']
    repl_metrics = metrics['replication_metrics']
    
    print(f"RTO Target: {metrics['rto_target_seconds']}s")
    print(f"RPO Target: {metrics['rpo_target_seconds']}s")
    print(f"\nReplication Status:")
    print(f"  Total Replicated: {repl_metrics['total_replicated']}")
    print(f"  Replication Lag: {repl_metrics['replication_lag_ms']:.1f}ms")
    print(f"  Compression Ratio: {repl_metrics['compression_ratio']*100:.1f}%")
    
    # 3. Trigger manual failover
    print_section("3️⃣ Triggering Manual Failover")
    print("Initiating failover...")
    response = requests.post(f"{API_URL}/api/trigger-failover")
    result = response.json()
    
    if result.get('status') == 'success':
        print(f"✅ Failover successful!")
        print(f"  From: {result['from_region']} → To: {result['to_region']}")
        print(f"  RTO: {result['rto_seconds']:.2f}s")
        print(f"  RPO: {result['rpo_seconds']:.2f}s")
    else:
        print(f"⚠️ Failover result: {result}")
    
    # Wait a bit
    time.sleep(2)
    
    # 4. Show updated status
    print_section("4️⃣ Post-Failover Status")
    response = requests.get(f"{API_URL}/api/status")
    status = response.json()
    print(f"New Primary Region: {status['primary_region']}")
    for region, details in status['regions'].items():
        print(f"  {region}: {details['role']} - {details['status']}")
    
    # 5. Run chaos test
    print_section("5️⃣ Running Chaos Engineering Test")
    print("Running network partition simulation...")
    response = requests.post(f"{API_URL}/api/chaos/run/network_partition")
    result = response.json()
    
    print(f"Test Result: {'✅ PASSED' if result.get('passed') else '❌ FAILED'}")
    if 'rto_seconds' in result:
        print(f"  RTO: {result['rto_seconds']:.2f}s")
    if 'rpo_seconds' in result:
        print(f"  RPO: {result['rpo_seconds']:.2f}s")
    
    # 6. Show final metrics
    print_section("6️⃣ Final Metrics Summary")
    response = requests.get(f"{API_URL}/api/metrics")
    metrics = response.json()
    dr_metrics = metrics['dr_metrics']
    
    print(f"Total Failovers: {dr_metrics['total_failovers']}")
    print(f"Successful: {dr_metrics['successful_failovers']}")
    print(f"Failed: {dr_metrics['failed_failovers']}")
    print(f"Average RTO: {dr_metrics['average_rto_seconds']:.2f}s")
    
    # 7. Show failover history
    print_section("7️⃣ Failover History")
    response = requests.get(f"{API_URL}/api/failover-history")
    history = response.json()
    
    print(f"Total Events: {history['total_count']}")
    for event in history['history'][:5]:
        timestamp = event['timestamp']
        from_region = event.get('from_region', 'N/A')
        to_region = event.get('to_region', 'N/A')
        status_val = event.get('status', 'unknown')
        print(f"\n  [{timestamp}]")
        print(f"  {from_region} → {to_region}")
        print(f"  Status: {status_val}")
        if 'rto_seconds' in event:
            print(f"  RTO: {event['rto_seconds']:.2f}s")
    
    print_section("✅ Demonstration Complete!")
    print("\n📊 View the dashboard at: http://localhost:3000")
    print("🔌 API documentation at: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(demonstrate_dr_system())
