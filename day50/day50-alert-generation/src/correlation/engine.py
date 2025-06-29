"""Alert correlation engine to group related alerts."""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import structlog
from config.database import Alert, get_db
from config.settings import settings

logger = structlog.get_logger()

class CorrelationEngine:
    def __init__(self):
        self.correlation_window = settings.CORRELATION_WINDOW
        self.active_correlations = defaultdict(list)
    
    async def correlate_alert(self, pattern_match: Dict) -> Optional[dict]:
        """Correlate incoming pattern match with existing alerts."""
        db = next(get_db())
        try:
            pattern_name = pattern_match['pattern_name']
            
            # Check for existing alert in correlation window
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.correlation_window)
            
            existing_alert = db.query(Alert).filter(
                Alert.pattern_name == pattern_name,
                Alert.last_occurrence >= cutoff_time,
                Alert.state.in_(['NEW', 'ACKNOWLEDGED', 'ESCALATED'])
            ).first()
            
            if existing_alert:
                # Update existing alert
                existing_alert.count += 1
                existing_alert.last_occurrence = datetime.utcnow()
                
                # Escalate if count exceeds threshold
                if existing_alert.count >= pattern_match['threshold'] * 2:
                    if existing_alert.state == 'NEW':
                        existing_alert.state = 'ESCALATED'
                        logger.warning("Alert escalated", 
                                     alert_id=existing_alert.id,
                                     pattern=pattern_name,
                                     count=existing_alert.count)
                
                db.commit()
                alert_dict = {
                    'id': existing_alert.id,
                    'count': existing_alert.count,
                    'state': existing_alert.state
                }
                return alert_dict
            else:
                # Create new alert
                alert = Alert(
                    pattern_name=pattern_name,
                    severity=pattern_match['severity'],
                    message=f"Pattern '{pattern_name}' detected in logs",
                    alert_metadata={
                        'threshold': pattern_match['threshold'],
                        'window': pattern_match['window'],
                        'sample_log': pattern_match['log_entry'].message[:200]
                    }
                )
                
                db.add(alert)
                db.commit()
                db.refresh(alert)
                
                logger.info("New alert created", 
                          alert_id=alert.id,
                          pattern=pattern_name,
                          severity=alert.severity)
                
                alert_dict = {
                    'id': alert.id,
                    'count': alert.count,
                    'state': alert.state
                }
                return alert_dict
                
        finally:
            db.close()
    
    async def group_related_alerts(self) -> List[Dict]:
        """Group alerts that might be related."""
        db = next(get_db())
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.correlation_window)
            
            active_alerts = db.query(Alert).filter(
                Alert.last_occurrence >= cutoff_time,
                Alert.state.in_(['NEW', 'ACKNOWLEDGED', 'ESCALATED'])
            ).all()
            
            # Group by severity and time proximity
            groups = defaultdict(list)
            for alert in active_alerts:
                time_bucket = int(alert.last_occurrence.timestamp() // 300) * 300  # 5-minute buckets
                key = f"{alert.severity}_{time_bucket}"
                groups[key].append(alert)
            
            # Return groups with multiple alerts
            return [alerts for alerts in groups.values() if len(alerts) > 1]
            
        finally:
            db.close()
    
    async def suppress_duplicate_alerts(self, pattern_name: str) -> bool:
        """Check if we should suppress alerts for rate limiting."""
        current_minute = int(datetime.utcnow().timestamp() // 60)
        key = f"{pattern_name}_{current_minute}"
        
        if key in self.active_correlations:
            count = len(self.active_correlations[key])
            if count >= settings.MAX_ALERTS_PER_MINUTE:
                logger.warning("Alert suppressed due to rate limit", 
                             pattern=pattern_name, count=count)
                return True
        
        self.active_correlations[key].append(datetime.utcnow())
        return False
