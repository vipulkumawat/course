import asyncio
from datetime import datetime
from typing import List, Dict
import statistics
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.sla_models import SLOViolation, MetricType, ServiceTier

class SLOEvaluator:
    def __init__(self, redis_client, metrics_collector, config: Dict):
        self.redis = redis_client
        self.metrics = metrics_collector
        self.config = config
        self.violations = {}
        self.running = False
        self.slo_targets = self._init_targets()
    
    def _init_targets(self):
        targets = {}
        for tier_name, cfg in self.config['service_tiers'].items():
            tier = ServiceTier(tier_name)
            targets[f"{tier_name}_availability"] = (tier, MetricType.AVAILABILITY, cfg['availability_slo'], "greater")
            targets[f"{tier_name}_latency"] = (tier, MetricType.LATENCY, cfg['latency_p95_ms'], "less")
            targets[f"{tier_name}_error_rate"] = (tier, MetricType.ERROR_RATE, cfg['error_rate_percent'], "less")
        return targets
    
    async def start_evaluation(self):
        self.running = True
        print("🎯 SLO evaluation started")
        while self.running:
            try:
                await self._evaluate_all()
                await asyncio.sleep(10)
            except Exception as e:
                print(f"Evaluation error: {e}")
                await asyncio.sleep(5)
    
    async def _evaluate_all(self):
        for slo_name, (tier, metric_type, target, comp) in self.slo_targets.items():
            metrics = await self.metrics.get_recent_metrics(tier, metric_type, 300)
            if not metrics:
                continue
            
            actual = self._calc_p95(metrics) if metric_type == MetricType.LATENCY else statistics.mean(metrics)
            violated = (actual > target) if comp == "less" else (actual < target)
            
            if violated:
                await self._handle_violation(slo_name, tier, actual, target)
            else:
                if slo_name in self.violations:
                    del self.violations[slo_name]
                    print(f"✅ Resolved: {slo_name}")
    
    def _calc_p95(self, vals: List[float]) -> float:
        sorted_vals = sorted(vals)
        idx = int(len(sorted_vals) * 0.95)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]
    
    async def _handle_violation(self, name: str, tier: ServiceTier, actual: float, target: float):
        if name in self.violations:
            self.violations[name].breach_duration_seconds += 10
            self.violations[name].actual_value = actual
        else:
            severity = "critical" if abs(actual - target) / target > 0.1 else "warning"
            self.violations[name] = SLOViolation(
                slo_name=name,
                service_tier=tier,
                actual_value=actual,
                target_value=target,
                breach_duration_seconds=10,
                severity=severity,
                timestamp=datetime.now()
            )
            print(f"🚨 NEW: {name} ({severity})")
    
    async def get_slo_status(self) -> Dict:
        status = {}
        for name, (tier, metric_type, target, comp) in self.slo_targets.items():
            metrics = await self.metrics.get_recent_metrics(tier, metric_type, 300)
            if metrics:
                current = self._calc_p95(metrics) if metric_type == MetricType.LATENCY else statistics.mean(metrics)
                compliant = (current <= target) if comp == "less" else (current >= target)
                status[name] = {
                    'tier': tier.value,
                    'type': metric_type.value,
                    'target': target,
                    'current': round(current, 2),
                    'compliant': compliant
                }
        return status
    
    async def get_violations(self) -> List[SLOViolation]:
        return list(self.violations.values())
    
    async def stop(self):
        self.running = False
