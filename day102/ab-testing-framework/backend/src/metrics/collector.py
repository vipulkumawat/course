import time
from typing import Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()

class MetricsCollector:
    def __init__(self):
        self.metrics_buffer = []
    
    def track_feature_flag_evaluation(self, flag_name: str, user_id: str, 
                                    is_enabled: bool, duration_ms: float):
        """Track feature flag evaluation metrics"""
        metric = {
            "type": "feature_flag_evaluation",
            "timestamp": datetime.utcnow().isoformat(),
            "flag_name": flag_name,
            "user_id": user_id,
            "is_enabled": is_enabled,
            "duration_ms": duration_ms,
            "service": "ab_testing_framework"
        }
        
        self.metrics_buffer.append(metric)
        logger.info("Feature flag evaluated", **metric)
    
    def track_user_interaction(self, user_id: str, experiment_id: int, 
                             variant: str, action: str, value: float = None):
        """Track user interaction for experiment analysis"""
        metric = {
            "type": "user_interaction",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": variant,
            "action": action,
            "value": value,
            "service": "ab_testing_framework"
        }
        
        self.metrics_buffer.append(metric)
        logger.info("User interaction tracked", **metric)
    
    def track_conversion_event(self, user_id: str, experiment_id: int, 
                             variant: str, conversion_type: str):
        """Track conversion events for experiment analysis"""
        metric = {
            "type": "conversion_event",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "experiment_id": experiment_id,
            "variant": variant,
            "conversion_type": conversion_type,
            "service": "ab_testing_framework"
        }
        
        self.metrics_buffer.append(metric)
        logger.info("Conversion event tracked", **metric)
    
    def flush_metrics(self):
        """Flush metrics buffer to external system"""
        if self.metrics_buffer:
            logger.info(f"Flushing {len(self.metrics_buffer)} metrics")
            # In real implementation, send to metrics pipeline
            self.metrics_buffer.clear()

metrics_collector = MetricsCollector()
