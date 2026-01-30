#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from main import app
    print("✓ Backend imports successful")
    
    # Test if we can get metrics
    from analytics.traffic_analyzer import TrafficAnalyzer
    analyzer = TrafficAnalyzer()
    metrics = analyzer.get_current_metrics()
    print(f"✓ Metrics generated: {metrics['total_connections']} connections, {metrics['total_bytes']} bytes")
    
    if metrics['total_connections'] == 0:
        print("⚠ Warning: Metrics are zero - traffic generator needs to run")
    else:
        print("✓ Metrics are non-zero")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
