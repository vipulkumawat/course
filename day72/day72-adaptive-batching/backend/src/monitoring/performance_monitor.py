"""
PerformanceMonitor: System-wide performance monitoring and alerting
"""

import asyncio
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class PerformanceAlert:
    timestamp: float
    severity: str  # "info", "warning", "critical"
    component: str
    metric: str
    current_value: float
    threshold: float
    message: str

@dataclass
class PerformanceReport:
    timestamp: float
    period_seconds: int
    throughput_avg: float
    throughput_max: float
    latency_avg: float
    latency_p95: float
    error_rate: float
    optimization_adjustments: int
    resource_efficiency: float

class PerformanceMonitor:
    """System-wide performance monitoring"""
    
    def __init__(self):
        self.running = False
        self.alerts: List[PerformanceAlert] = []
        self.performance_reports: List[PerformanceReport] = []
        
        # Alert thresholds
        self.thresholds = {
            "cpu_usage_warning": 70.0,
            "cpu_usage_critical": 85.0,
            "memory_usage_warning": 75.0,
            "memory_usage_critical": 90.0,
            "latency_warning": 500.0,  # ms
            "latency_critical": 1000.0,  # ms
            "error_rate_warning": 0.01,  # 1%
            "error_rate_critical": 0.05,  # 5%
            "throughput_degradation": 0.20  # 20% drop
        }
        
        # Performance baselines
        self.baseline_throughput = None
        self.baseline_latency = None
        
    async def start(self):
        """Start performance monitoring"""
        self.running = True
        logger.info("Starting performance monitor")
        
        await asyncio.gather(
            self._monitoring_loop(),
            self._reporting_loop()
        )
    
    async def stop(self):
        """Stop performance monitoring"""
        self.running = False
        logger.info("Performance monitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                # Monitoring logic would go here
                # For now, just a placeholder
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    async def _reporting_loop(self):
        """Generate periodic performance reports"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Report every minute
                
                report = self._generate_performance_report()
                self.performance_reports.append(report)
                
                # Trim old reports
                if len(self.performance_reports) > 1440:  # Keep 24 hours
                    self.performance_reports.pop(0)
                
                logger.debug(f"Generated performance report: "
                           f"throughput={report.throughput_avg:.1f}, "
                           f"latency={report.latency_avg:.1f}ms")
                
            except Exception as e:
                logger.error(f"Error in reporting loop: {e}")
                await asyncio.sleep(60)
    
    def _generate_performance_report(self) -> PerformanceReport:
        """Generate a performance report for the last period"""
        return PerformanceReport(
            timestamp=time.time(),
            period_seconds=60,
            throughput_avg=0.0,  # Would be calculated from actual metrics
            throughput_max=0.0,
            latency_avg=0.0,
            latency_p95=0.0,
            error_rate=0.0,
            optimization_adjustments=0,
            resource_efficiency=0.0
        )
    
    def get_performance_stats(self) -> Dict:
        """Get current performance statistics"""
        recent_alerts = [alert for alert in self.alerts if alert.timestamp > time.time() - 3600]
        recent_reports = [report for report in self.performance_reports if report.timestamp > time.time() - 3600]
        
        return {
            "alerts": {
                "total": len(self.alerts),
                "recent": len(recent_alerts),
                "recent_alerts": [asdict(alert) for alert in recent_alerts[-10:]]
            },
            "reports": {
                "total": len(self.performance_reports),
                "recent": len(recent_reports),
                "latest_report": asdict(recent_reports[-1]) if recent_reports else None
            },
            "thresholds": self.thresholds,
            "baselines": {
                "throughput": self.baseline_throughput,
                "latency": self.baseline_latency
            }
        }
