import asyncio
import json
import logging
from typing import Dict, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import redis
from enum import Enum

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AlertCondition:
    name: str
    threshold: float
    metric_key: str
    severity: AlertSeverity
    cooldown_minutes: int = 30
    notification_channels: List[str] = None

@dataclass
class Alert:
    condition_name: str
    severity: AlertSeverity
    current_value: float
    threshold: float
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

class AlertEvaluator:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.conditions: Dict[str, AlertCondition] = {}
        self.alert_history: List[Alert] = []
        self.suppressed_alerts: Dict[str, datetime] = {}
        
    def add_condition(self, condition: AlertCondition):
        """Add new alert condition"""
        self.conditions[condition.name] = condition
        logging.info(f"📋 Added alert condition: {condition.name}")
    
    async def evaluate_metrics(self, metrics: Dict[str, float]) -> List[Alert]:
        """Evaluate current metrics against alert conditions"""
        triggered_alerts = []
        
        for condition_name, condition in self.conditions.items():
            if condition.metric_key not in metrics:
                continue
                
            current_value = metrics[condition.metric_key]
            
            # Check if condition is met
            if self._should_trigger_alert(condition, current_value):
                # Check cooldown period
                if self._is_in_cooldown(condition_name, condition.cooldown_minutes):
                    continue
                
                alert = Alert(
                    condition_name=condition_name,
                    severity=condition.severity,
                    current_value=current_value,
                    threshold=condition.threshold,
                    message=self._generate_alert_message(condition, current_value),
                    timestamp=datetime.now(),
                    metadata={'metric_key': condition.metric_key}
                )
                
                triggered_alerts.append(alert)
                self.alert_history.append(alert)
                self.suppressed_alerts[condition_name] = datetime.now()
                
                logging.warning(f"🚨 Alert triggered: {alert.message}")
        
        return triggered_alerts
    
    def _should_trigger_alert(self, condition: AlertCondition, current_value: float) -> bool:
        """Determine if alert should be triggered based on condition"""
        if condition.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]:
            return current_value > condition.threshold
        elif condition.severity == AlertSeverity.WARNING:
            return current_value > condition.threshold * 0.8
        return current_value > condition.threshold * 0.6
    
    def _is_in_cooldown(self, condition_name: str, cooldown_minutes: int) -> bool:
        """Check if alert is in cooldown period"""
        if condition_name not in self.suppressed_alerts:
            return False
        
        last_triggered = self.suppressed_alerts[condition_name]
        cooldown_period = timedelta(minutes=cooldown_minutes)
        return datetime.now() - last_triggered < cooldown_period
    
    def _generate_alert_message(self, condition: AlertCondition, current_value: float) -> str:
        """Generate human-readable alert message"""
        return (f"{condition.name}: {current_value:.2f} exceeds threshold of "
                f"{condition.threshold:.2f} (Severity: {condition.severity.value})")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Get alerts from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of recent alert activity"""
        recent_alerts = self.get_recent_alerts(24)
        
        summary = {
            'total_alerts': len(recent_alerts),
            'by_severity': {
                'critical': len([a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]),
                'error': len([a for a in recent_alerts if a.severity == AlertSeverity.ERROR]),
                'warning': len([a for a in recent_alerts if a.severity == AlertSeverity.WARNING]),
                'info': len([a for a in recent_alerts if a.severity == AlertSeverity.INFO])
            },
            'most_frequent': self._get_most_frequent_alerts(recent_alerts)
        }
        
        return summary
    
    def _get_most_frequent_alerts(self, alerts: List[Alert]) -> Dict[str, int]:
        """Get most frequently triggered alert conditions"""
        frequency = {}
        for alert in alerts:
            frequency[alert.condition_name] = frequency.get(alert.condition_name, 0) + 1
        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:5])
