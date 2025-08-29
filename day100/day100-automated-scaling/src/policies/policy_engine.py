import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from src.monitoring.metrics_collector import ComponentMetrics

class ScalingAction(Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"

@dataclass
class ScalingDecision:
    component_id: str
    action: ScalingAction
    target_instances: int
    current_instances: int
    reason: str
    confidence: float
    timestamp: float

class PolicyEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.policies = config.get('scaling_policies', {})
        self.thresholds = config.get('thresholds', {})
        self.cooldown_tracker = {}
        self.scaling_history = []
        
    def evaluate_scaling_policies(self, metrics: Dict[str, ComponentMetrics]) -> List[ScalingDecision]:
        """Evaluate all scaling policies and return decisions"""
        decisions = []
        current_time = time.time()
        
        for component_id, component_metrics in metrics.items():
            decision = self._evaluate_component_policy(component_metrics, current_time)
            if decision.action != ScalingAction.NO_ACTION:
                decisions.append(decision)
                
        return decisions
    
    def _evaluate_component_policy(self, metrics: ComponentMetrics, 
                                  current_time: float) -> ScalingDecision:
        """Evaluate scaling policy for a single component"""
        component_type = metrics.component_type
        policy = self.policies.get(component_type, {})
        
        if not policy:
            return ScalingDecision(
                component_id=metrics.component_id,
                action=ScalingAction.NO_ACTION,
                target_instances=metrics.instance_count,
                current_instances=metrics.instance_count,
                reason="No policy defined",
                confidence=0.0,
                timestamp=current_time
            )
        
        # Check cooldown period
        if self._is_in_cooldown(metrics.component_id, current_time):
            return ScalingDecision(
                component_id=metrics.component_id,
                action=ScalingAction.NO_ACTION,
                target_instances=metrics.instance_count,
                current_instances=metrics.instance_count,
                reason="In cooldown period",
                confidence=0.0,
                timestamp=current_time
            )
        
        # Evaluate scale-up conditions
        scale_up_triggers = []
        if metrics.cpu_percent > policy.get('target_cpu_utilization', 70):
            scale_up_triggers.append(f"CPU {metrics.cpu_percent:.1f}%")
            
        if metrics.queue_depth > policy.get('target_queue_depth', 1000):
            scale_up_triggers.append(f"Queue depth {metrics.queue_depth}")
            
        if metrics.response_time_ms > self.thresholds.get('response_time', {}).get('warning', 1000):
            scale_up_triggers.append(f"Response time {metrics.response_time_ms:.1f}ms")
        
        # Evaluate scale-down conditions
        scale_down_triggers = []
        if (metrics.cpu_percent < policy.get('target_cpu_utilization', 70) * 0.5 and
            metrics.queue_depth < policy.get('target_queue_depth', 1000) * 0.3):
            scale_down_triggers.append("Low utilization")
        
        # Make scaling decision
        if scale_up_triggers and metrics.instance_count < policy.get('max_instances', 10):
            return self._create_scale_up_decision(metrics, policy, scale_up_triggers, current_time)
        elif scale_down_triggers and metrics.instance_count > policy.get('min_instances', 1):
            return self._create_scale_down_decision(metrics, policy, scale_down_triggers, current_time)
        else:
            return ScalingDecision(
                component_id=metrics.component_id,
                action=ScalingAction.NO_ACTION,
                target_instances=metrics.instance_count,
                current_instances=metrics.instance_count,
                reason="Within acceptable ranges",
                confidence=1.0,
                timestamp=current_time
            )
    
    def _create_scale_up_decision(self, metrics: ComponentMetrics, policy: Dict,
                                 triggers: List[str], current_time: float) -> ScalingDecision:
        """Create a scale-up decision"""
        # Calculate target instances based on load
        cpu_ratio = metrics.cpu_percent / policy.get('target_cpu_utilization', 70)
        queue_ratio = metrics.queue_depth / policy.get('target_queue_depth', 1000)
        
        scaling_factor = max(cpu_ratio, queue_ratio, 1.2)  # At least 20% increase
        
        # Ensure we always scale up by at least 1 instance
        target_instances = max(
            int(metrics.instance_count * scaling_factor),
            metrics.instance_count + 1
        )
        
        # Cap at maximum instances
        target_instances = min(target_instances, policy.get('max_instances', 10))
        
        confidence = min(max(cpu_ratio, queue_ratio) - 1.0, 1.0)
        
        return ScalingDecision(
            component_id=metrics.component_id,
            action=ScalingAction.SCALE_UP,
            target_instances=target_instances,
            current_instances=metrics.instance_count,
            reason=f"Scale up due to: {', '.join(triggers)}",
            confidence=confidence,
            timestamp=current_time
        )
    
    def _create_scale_down_decision(self, metrics: ComponentMetrics, policy: Dict,
                                   triggers: List[str], current_time: float) -> ScalingDecision:
        """Create a scale-down decision"""
        target_instances = max(
            metrics.instance_count - 1,
            policy.get('min_instances', 1)
        )
        
        return ScalingDecision(
            component_id=metrics.component_id,
            action=ScalingAction.SCALE_DOWN,
            target_instances=target_instances,
            current_instances=metrics.instance_count,
            reason=f"Scale down due to: {', '.join(triggers)}",
            confidence=0.8,
            timestamp=current_time
        )
    
    def _is_in_cooldown(self, component_id: str, current_time: float) -> bool:
        """Check if component is in cooldown period"""
        if component_id not in self.cooldown_tracker:
            return False
            
        last_action_time = self.cooldown_tracker[component_id]['time']
        last_action = self.cooldown_tracker[component_id]['action']
        
        if last_action == ScalingAction.SCALE_UP:
            cooldown = self.policies.get('log_processors', {}).get('scale_up_cooldown', 300)
        else:
            cooldown = self.policies.get('log_processors', {}).get('scale_down_cooldown', 600)
        
        return (current_time - last_action_time) < cooldown
    
    def record_scaling_action(self, decision: ScalingDecision):
        """Record a scaling action for cooldown tracking"""
        self.cooldown_tracker[decision.component_id] = {
            'time': decision.timestamp,
            'action': decision.action
        }
        self.scaling_history.append(decision)
        
        # Keep only recent history
        if len(self.scaling_history) > 100:
            self.scaling_history = self.scaling_history[-50:]
