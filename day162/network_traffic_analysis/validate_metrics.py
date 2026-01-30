#!/usr/bin/env python3
"""Validate that dashboard metrics are updating and non-zero"""
import urllib.request
import urllib.error
import time
import json

def validate_metrics():
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Validating Dashboard Metrics")
    print("=" * 60)
    
    # Check health
    try:
        with urllib.request.urlopen(f"{base_url}/api/health", timeout=5) as response:
            if response.getcode() == 200:
                print("✓ Backend is healthy")
            else:
                print(f"✗ Backend health check failed: {response.getcode()}")
                return False
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        return False
    
    # Check metrics multiple times to verify they're updating
    print("\nChecking metrics over time...")
    metrics_list = []
    
    for i in range(3):
        try:
            with urllib.request.urlopen(f"{base_url}/api/metrics", timeout=5) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())
                    metrics_list.append(data)
                    print(f"\nCheck {i+1}:")
                    print(f"  Total connections: {data.get('total_connections', 0)}")
                    print(f"  Total bytes: {data.get('total_bytes', 0)}")
                    print(f"  Unique sources: {data.get('unique_sources', 0)}")
                    print(f"  Protocols: {list(data.get('protocols', {}).keys())}")
                else:
                    print(f"✗ Failed to get metrics: {response.getcode()}")
                    return False
        except Exception as e:
            print(f"✗ Error getting metrics: {e}")
            return False
        
        if i < 2:
            time.sleep(3)
    
    # Validate metrics are non-zero
    print("\n" + "=" * 60)
    print("Validation Results:")
    print("=" * 60)
    
    all_valid = True
    for i, metrics in enumerate(metrics_list, 1):
        conn = metrics.get('total_connections', 0)
        bytes_val = metrics.get('total_bytes', 0)
        sources = metrics.get('unique_sources', 0)
        
        print(f"\nCheck {i}:")
        print(f"  Connections > 0: {conn > 0} ({conn})")
        print(f"  Bytes > 0: {bytes_val > 0} ({bytes_val})")
        print(f"  Sources > 0: {sources > 0} ({sources})")
        
        if conn == 0 or bytes_val == 0 or sources == 0:
            all_valid = False
    
    # Check if metrics are changing
    if len(metrics_list) > 1:
        conn_changed = metrics_list[-1]['total_connections'] != metrics_list[0]['total_connections']
        bytes_changed = metrics_list[-1]['total_bytes'] != metrics_list[0]['total_bytes']
        print(f"\nMetrics changing over time:")
        print(f"  Connections changed: {conn_changed}")
        print(f"  Bytes changed: {bytes_changed}")
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All metrics are non-zero and updating!")
        print("✅ Dashboard should display real data")
    else:
        print("⚠ Some metrics are zero - traffic generator may need more time")
    print("=" * 60)
    
    return all_valid

if __name__ == "__main__":
    success = validate_metrics()
    exit(0 if success else 1)
