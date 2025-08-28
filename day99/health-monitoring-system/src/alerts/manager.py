import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    component_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict = None

class AlertRule:
    def __init__(self, name: str, metric_name: str, threshold: float, 
                 severity: AlertSeverity, comparison: str = "gt"):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.severity = severity
        self.comparison = comparison  # gt, lt, eq
        
    def evaluate(self, value: float) -> bool:
        """Evaluate if the rule should trigger"""
        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        elif self.comparison == "eq":
            return value == self.threshold
        return False

class AlertManager:
    def __init__(self, config):
        self.config = config
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []
        self.suppressed_alerts: Dict[str, datetime] = {}
        self.running = False
        
    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
        
    def add_notification_handler(self, handler: Callable):
        """Add a notification handler function"""
        self.notification_handlers.append(handler)
        
    async def start(self):
        """Start the alert manager"""
        self.running = True
        
        # Initialize default rules
        self._setup_default_rules()
        
        logger.info("Alert manager started")
        
    async def stop(self):
        """Stop the alert manager"""
        self.running = False
        logger.info("Alert manager stopped")
        
    def _setup_default_rules(self):
        """Setup default monitoring rules"""
        # CPU rules
        self.add_rule(AlertRule(
            "High CPU Usage Warning",
            "cpu_percent",
            self.config.cpu_warning_threshold,
            AlertSeverity.WARNING
        ))
        
        self.add_rule(AlertRule(
            "Critical CPU Usage",
            "cpu_percent", 
            self.config.cpu_critical_threshold,
            AlertSeverity.CRITICAL
        ))
        
        # Memory rules
        self.add_rule(AlertRule(
            "High Memory Usage Warning",
            "memory_percent",
            self.config.memory_warning_threshold,
            AlertSeverity.WARNING
        ))
        
        self.add_rule(AlertRule(
            "Critical Memory Usage",
            "memory_percent",
            self.config.memory_critical_threshold,
            AlertSeverity.CRITICAL
        ))
        
        # Disk rules
        self.add_rule(AlertRule(
            "High Disk Usage Warning",
            "disk_percent",
            self.config.disk_warning_threshold,
            AlertSeverity.WARNING
        ))
        
        self.add_rule(AlertRule(
            "Critical Disk Usage",
            "disk_percent",
            self.config.disk_critical_threshold,
            AlertSeverity.CRITICAL
        ))
        
    async def evaluate_metrics(self, system_metrics, component_health):
        """Evaluate metrics against alert rules"""
        current_time = datetime.now()
        
        # Evaluate system metrics
        if system_metrics:
            await self._evaluate_system_alerts(system_metrics, current_time)
            
        # Evaluate component health
        for component_id, health in component_health.items():
            await self._evaluate_component_alerts(component_id, health, current_time)
            
    async def _evaluate_system_alerts(self, metrics, current_time):
        """Evaluate system-level alerts"""
        metric_values = {
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_percent": metrics.disk_percent
        }
        
        for rule in self.rules:
            if rule.metric_name in metric_values:
                value = metric_values[rule.metric_name]
                
                if rule.evaluate(value):
                    await self._create_alert(
                        rule, "system", value, current_time
                    )
                else:
                    # Check if we should resolve existing alert
                    await self._check_alert_resolution(rule, "system")
                    
    async def _evaluate_component_alerts(self, component_id, health, current_time):
        """Evaluate component-specific alerts"""
        # Component availability alert
        if health.status.value in ["critical", "unknown"]:
            await self._create_component_alert(
                component_id,
                "Component Unavailable",
                f"Component {health.name} is {health.status.value}",
                AlertSeverity.CRITICAL,
                current_time
            )
        elif health.status.value == "warning":
            await self._create_component_alert(
                component_id,
                "Component Warning",
                f"Component {health.name} is in warning state",
                AlertSeverity.WARNING,
                current_time
            )
            
    async def _create_alert(self, rule: AlertRule, component_id: str, 
                           value: float, timestamp: datetime):
        """Create a new alert"""
        alert_key = f"{component_id}_{rule.name}"
        
        # Check if alert is suppressed
        if self._is_alert_suppressed(alert_key, timestamp):
            return
            
        # Check if alert already exists
        if alert_key in self.active_alerts:
            return
            
        alert_id = f"alert_{int(timestamp.timestamp())}_{hash(alert_key)}"
        
        alert = Alert(
            id=alert_id,
            title=rule.name,
            description=f"{rule.metric_name} is {value:.2f}, threshold is {rule.threshold}",
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            component_id=component_id,
            metric_name=rule.metric_name,
            current_value=value,
            threshold_value=rule.threshold,
            created_at=timestamp,
            metadata={"rule": rule.name}
        )
        
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.warning(f"Alert created: {alert.title} for {component_id}")
        
    async def _create_component_alert(self, component_id: str, title: str,
                                    description: str, severity: AlertSeverity,
                                    timestamp: datetime):
        """Create component-specific alert"""
        alert_key = f"{component_id}_{title}"
        
        if alert_key in self.active_alerts:
            return
            
        alert_id = f"alert_{int(timestamp.timestamp())}_{hash(alert_key)}"
        
        alert = Alert(
            id=alert_id,
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.ACTIVE,
            component_id=component_id,
            metric_name="availability",
            current_value=0.0,
            threshold_value=1.0,
            created_at=timestamp,
            metadata={"type": "component"}
        )
        
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        await self._send_notifications(alert)
        
    async def _check_alert_resolution(self, rule: AlertRule, component_id: str):
        """Check if an alert should be resolved"""
        alert_key = f"{component_id}_{rule.name}"
        
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[alert_key]
            
            logger.info(f"Alert resolved: {alert.title} for {component_id}")
            
    def _is_alert_suppressed(self, alert_key: str, timestamp: datetime) -> bool:
        """Check if alert is in suppression period"""
        if alert_key in self.suppressed_alerts:
            suppress_until = self.suppressed_alerts[alert_key]
            if timestamp < suppress_until:
                return True
            else:
                del self.suppressed_alerts[alert_key]
        return False
        
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications to registered handlers"""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
                
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an active alert"""
        for alert in self.active_alerts.values():
            if alert.id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                logger.info(f"Alert acknowledged: {alert.title}")
                return True
        return False
        
    def suppress_alert(self, alert_key: str, duration_minutes: int):
        """Suppress alerts for a specific key"""
        suppress_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.suppressed_alerts[alert_key] = suppress_until
        logger.info(f"Alert suppressed: {alert_key} until {suppress_until}")
        
    def get_alert_summary(self) -> Dict:
        """Get alert summary statistics"""
        active_count = len(self.active_alerts)
        critical_count = len([
            a for a in self.active_alerts.values() 
            if a.severity == AlertSeverity.CRITICAL
        ])
        
        recent_alerts = [
            asdict(alert) for alert in self.alert_history[-10:]
        ]
        
        return {
            "active_alerts": active_count,
            "critical_alerts": critical_count,
            "total_alerts_today": len([
                a for a in self.alert_history 
                if a.created_at.date() == datetime.now().date()
            ]),
            "recent_alerts": recent_alerts,
            "active_alert_list": [
                asdict(alert) for alert in self.active_alerts.values()
            ]
        }
