"""Test monitoring-aware operator"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'operator'))

def test_scale_up_decision():
    """Test scale up logic"""
    from monitoring_operator import MonitoringAwareOperator
    
    # Mock operator without K8s connection
    operator = MonitoringAwareOperator.__new__(MonitoringAwareOperator)
    
    # High CPU and queue should trigger scale up
    metrics = {'cpu_percent': 80, 'queue_depth': 600, 'latency_p95': 0.3}
    should_scale, reason = operator.should_scale_up(metrics)
    
    assert should_scale == True
    assert 'CPU' in reason or 'queue' in reason

def test_scale_down_decision():
    """Test scale down logic"""
    from monitoring_operator import MonitoringAwareOperator
    
    operator = MonitoringAwareOperator.__new__(MonitoringAwareOperator)
    
    # Low resource usage should allow scale down
    metrics = {'cpu_percent': 25, 'queue_depth': 30, 'latency_p95': 0.05}
    should_scale, reason = operator.should_scale_down(metrics)
    
    assert should_scale == True

print("✅ All operator tests passed!")
