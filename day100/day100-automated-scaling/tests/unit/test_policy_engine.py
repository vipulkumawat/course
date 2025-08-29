import pytest
import time
from src.policies.policy_engine import PolicyEngine, ScalingAction
from src.monitoring.metrics_collector import ComponentMetrics

@pytest.fixture
def policy_engine():
    config = {
        'scaling_policies': {
            'log_processors': {
                'min_instances': 2,
                'max_instances': 10,
                'target_cpu_utilization': 70,
                'target_queue_depth': 1000,
                'scale_up_cooldown': 300,
                'scale_down_cooldown': 600
            }
        },
        'thresholds': {
            'response_time': {'warning': 1000}
        }
    }
    return PolicyEngine(config)

def test_scale_up_decision(policy_engine):
    """Test scale up decision when CPU is high"""
    metrics = ComponentMetrics(
        component_id="test-processor",
        component_type="log_processors",
        timestamp=time.time(),
        cpu_percent=85.0,  # Above 70% threshold
        memory_percent=60.0,
        queue_depth=1200,  # Above 1000 threshold
        response_time_ms=500.0,
        instance_count=2
    )
    
    decision = policy_engine._evaluate_component_policy(metrics, time.time())
    assert decision.action == ScalingAction.SCALE_UP
    assert decision.target_instances > 2

def test_scale_down_decision(policy_engine):
    """Test scale down decision when utilization is low"""
    metrics = ComponentMetrics(
        component_id="test-processor",
        component_type="log_processors",
        timestamp=time.time(),
        cpu_percent=20.0,  # Well below threshold
        memory_percent=30.0,
        queue_depth=100,   # Well below threshold
        response_time_ms=50.0,
        instance_count=5   # Above minimum
    )
    
    decision = policy_engine._evaluate_component_policy(metrics, time.time())
    assert decision.action == ScalingAction.SCALE_DOWN
    assert decision.target_instances < 5

def test_no_action_in_cooldown(policy_engine):
    """Test that no action is taken during cooldown period"""
    # Record a recent scaling action
    current_time = time.time()
    policy_engine.cooldown_tracker["test-processor"] = {
        'time': current_time - 100,  # 100 seconds ago
        'action': ScalingAction.SCALE_UP
    }
    
    metrics = ComponentMetrics(
        component_id="test-processor",
        component_type="log_processors",
        timestamp=current_time,
        cpu_percent=95.0,  # Very high CPU
        memory_percent=90.0,
        queue_depth=2000,  # Very high queue
        instance_count=2
    )
    
    decision = policy_engine._evaluate_component_policy(metrics, current_time)
    assert decision.action == ScalingAction.NO_ACTION
    assert "cooldown" in decision.reason.lower()
