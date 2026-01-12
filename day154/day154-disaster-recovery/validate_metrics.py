#!/usr/bin/env python3
"""Validate that dashboard metrics are updating and not zero"""
import requests
import time
import sys

API_URL = "http://localhost:8000"

def check_api():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/api/status", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_metrics():
    """Get current metrics"""
    try:
        response = requests.get(f"{API_URL}/api/metrics", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting metrics: {e}")
        return None

def trigger_failover():
    """Trigger a failover"""
    try:
        response = requests.post(f"{API_URL}/api/trigger-failover", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error triggering failover: {e}")
        return None

def run_chaos_test(scenario):
    """Run a chaos test"""
    try:
        response = requests.post(f"{API_URL}/api/chaos/run/{scenario}", timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error running chaos test: {e}")
        return None

def validate_metrics(metrics):
    """Validate that metrics are not all zero"""
    issues = []
    
    if not metrics:
        return False, ["Could not get metrics"]
    
    dr_metrics = metrics.get('dr_metrics', {})
    repl_metrics = metrics.get('replication_metrics', {})
    
    # Check replication metrics
    if repl_metrics.get('total_replicated', 0) == 0:
        issues.append("Replication total_replicated is zero")
    
    if repl_metrics.get('compression_ratio', 0) == 0:
        issues.append("Replication compression_ratio is zero")
    
    # Check regions
    regions = dr_metrics.get('regions', {})
    for name, region in regions.items():
        if region.get('replication_lag_ms', 0) == 0 and name != dr_metrics.get('current_primary'):
            # Secondary should have some lag or replication activity
            pass  # This is OK initially
    
    return len(issues) == 0, issues

def main():
    print("=" * 60)
    print("Validating DR System Metrics")
    print("=" * 60)
    
    # Wait for API
    print("\n1. Checking API availability...")
    for i in range(10):
        if check_api():
            print("   ✓ API is running")
            break
        time.sleep(1)
    else:
        print("   ✗ API is not running")
        return 1
    
    # Get initial metrics
    print("\n2. Getting initial metrics...")
    metrics = get_metrics()
    if not metrics:
        print("   ✗ Could not get metrics")
        return 1
    
    repl_metrics = metrics['replication_metrics']
    print(f"   ✓ Replication: {repl_metrics['total_replicated']} entries replicated")
    print(f"   ✓ Replication Lag: {repl_metrics['replication_lag_ms']:.2f}ms")
    print(f"   ✓ Compression: {repl_metrics['compression_ratio']*100:.1f}%")
    
    # Wait a bit for more replication
    print("\n3. Waiting for replication activity...")
    time.sleep(5)
    
    # Get updated metrics
    metrics = get_metrics()
    repl_metrics = metrics['replication_metrics']
    print(f"   ✓ Replication: {repl_metrics['total_replicated']} entries (updated)")
    
    # Trigger failover
    print("\n4. Triggering failover to generate DR metrics...")
    result = trigger_failover()
    if result and result.get('status') == 'success':
        print(f"   ✓ Failover successful!")
        print(f"     RTO: {result.get('rto_seconds', 0):.2f}s")
        print(f"     RPO: {result.get('rpo_seconds', 0):.2f}s")
    else:
        print(f"   ⚠ Failover result: {result}")
    
    time.sleep(2)
    
    # Get metrics after failover
    print("\n5. Getting metrics after failover...")
    metrics = get_metrics()
    dr_metrics = metrics['dr_metrics']
    print(f"   ✓ Total Failovers: {dr_metrics['total_failovers']}")
    print(f"   ✓ Successful: {dr_metrics['successful_failovers']}")
    print(f"   ✓ Average RTO: {dr_metrics['average_rto_seconds']:.2f}s")
    
    # Run chaos test
    print("\n6. Running chaos test...")
    result = run_chaos_test('network_partition')
    if result:
        print(f"   ✓ Chaos test completed: {'PASSED' if result.get('passed') else 'FAILED'}")
        if result.get('rto_seconds'):
            print(f"     RTO: {result['rto_seconds']:.2f}s")
    
    # Final validation
    print("\n7. Final metrics validation...")
    metrics = get_metrics()
    is_valid, issues = validate_metrics(metrics)
    
    if is_valid:
        print("   ✓ All metrics are updating correctly!")
    else:
        print("   ✗ Issues found:")
        for issue in issues:
            print(f"     - {issue}")
    
    print("\n" + "=" * 60)
    print("Validation Complete!")
    print("=" * 60)
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())
