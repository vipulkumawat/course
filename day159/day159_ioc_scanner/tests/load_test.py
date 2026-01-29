#!/usr/bin/env python3
import time
import random
import requests
import json
from concurrent.futures import ThreadPoolExecutor
import sys

API_URL = "http://localhost:8000/scan"

def generate_sample_logs(count):
    """Generate sample logs for testing"""
    malicious_ips = ["192.168.1.100", "10.0.0.666", "172.16.0.50"]
    normal_ips = ["8.8.8.8", "1.1.1.1", "192.168.1.1"]
    
    logs = []
    for i in range(count):
        ip = random.choice(malicious_ips + normal_ips)
        logs.append({
            "id": i,
            "ip": ip,
            "action": random.choice(["login", "download", "upload"]),
            "timestamp": time.time()
        })
    
    return logs

def scan_batch(logs):
    """Scan a batch of logs"""
    try:
        response = requests.post(
            API_URL,
            json={"logs": logs},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("🔥 IOC Scanner Load Test")
    print("="*50)
    
    total_logs = 1000
    batch_size = 100
    
    print(f"Generating {total_logs} sample logs...")
    all_logs = generate_sample_logs(total_logs)
    
    batches = [all_logs[i:i+batch_size] for i in range(0, total_logs, batch_size)]
    
    print(f"Scanning {len(batches)} batches of {batch_size} logs each...")
    start_time = time.time()
    
    total_alerts = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(scan_batch, batches))
    
    end_time = time.time()
    duration = end_time - start_time
    
    for result in results:
        if result:
            total_alerts += result.get("alert_count", 0)
    
    throughput = total_logs / duration
    
    print(f"\n✅ Load Test Complete!")
    print(f"Total logs scanned: {total_logs}")
    print(f"Total alerts generated: {total_alerts}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Throughput: {throughput:.1f} logs/second")
    
    if throughput >= 100:
        print("✅ Performance target met (>100 logs/sec)")
        sys.exit(0)
    else:
        print("⚠️  Performance below target")
        sys.exit(1)

if __name__ == "__main__":
    main()
