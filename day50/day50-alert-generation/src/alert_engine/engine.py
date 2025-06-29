"""Main alert generation engine."""
import asyncio
from typing import List, Dict
import structlog
from datetime import datetime, timedelta
from src.pattern_matching.engine import PatternMatcher
from src.correlation.engine import CorrelationEngine
from src.alert_engine.notification import NotificationManager
from config.database import LogEntry, Alert, get_db

logger = structlog.get_logger()

class AlertEngine:
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.correlation_engine = CorrelationEngine()
        self.notification_manager = NotificationManager()
        self.running = False
    
    async def start(self):
        """Start the alert engine."""
        self.running = True
        logger.info("Alert engine started")
        
        # Start background tasks
        await asyncio.gather(
            self.process_logs(),
            self.cleanup_old_correlations(),
            self.check_alert_escalations()
        )
    
    async def stop(self):
        """Stop the alert engine."""
        self.running = False
        logger.info("Alert engine stopped")
    
    async def process_logs(self):
        """Main log processing loop."""
        while self.running:
            try:
                db = next(get_db())
                try:
                    # Get unprocessed logs
                    unprocessed_logs = db.query(LogEntry).filter(
                        LogEntry.processed == False
                    ).limit(100).all()
                    
                    for log_entry in unprocessed_logs:
                        await self.process_single_log(log_entry)
                        log_entry.processed = True
                    
                    db.commit()
                    
                finally:
                    db.close()
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error("Error processing logs", error=str(e))
                await asyncio.sleep(5)
    
    async def process_single_log(self, log_entry: LogEntry):
        """Process a single log entry for alerts."""
        try:
            # Analyze log against patterns
            pattern_matches = await self.pattern_matcher.analyze_log(log_entry)
            
            for match in pattern_matches:
                # Check if threshold is exceeded
                current_count = await self.pattern_matcher.check_threshold(
                    match['pattern_name'], 
                    match['window']
                )
                
                if current_count >= match['threshold']:
                    # Check for rate limiting
                    if not await self.correlation_engine.suppress_duplicate_alerts(
                        match['pattern_name']
                    ):
                        # Create or update alert
                        alert = await self.correlation_engine.correlate_alert(match)
                        
                        if alert and alert['count'] == 1:  # New alert
                            await self.notification_manager.send_alert(alert)
                        elif alert and alert['state'] == 'ESCALATED':
                            await self.notification_manager.send_escalation(alert)
        
        except Exception as e:
            logger.error("Error processing log entry", 
                        log_id=log_entry.id, 
                        error=str(e))
    
    async def cleanup_old_correlations(self):
        """Clean up old correlation data."""
        while self.running:
            try:
                current_time = datetime.utcnow()
                # Clean up correlation data older than 1 hour
                cutoff = current_time.timestamp() - 3600
                
                keys_to_remove = []
                for key, timestamps in self.correlation_engine.active_correlations.items():
                    filtered_timestamps = [
                        ts for ts in timestamps 
                        if ts.timestamp() > cutoff
                    ]
                    if filtered_timestamps:
                        self.correlation_engine.active_correlations[key] = filtered_timestamps
                    else:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.correlation_engine.active_correlations[key]
                
                logger.debug("Cleaned up old correlations", removed=len(keys_to_remove))
                
            except Exception as e:
                logger.error("Error cleaning correlations", error=str(e))
            
            await asyncio.sleep(300)  # Clean every 5 minutes
    
    async def check_alert_escalations(self):
        """Check for alerts that need escalation."""
        while self.running:
            try:
                db = next(get_db())
                try:
                    # Find alerts that have been NEW for too long
                    cutoff_time = datetime.utcnow() - timedelta(minutes=15)
                    
                    stale_alerts = db.query(Alert).filter(
                        Alert.state == 'NEW',
                        Alert.first_occurrence <= cutoff_time
                    ).all()
                    
                    for alert in stale_alerts:
                        alert.state = 'ESCALATED'
                        await self.notification_manager.send_escalation(alert)
                        logger.warning("Alert auto-escalated", alert_id=alert.id)
                    
                    db.commit()
                    
                finally:
                    db.close()
                
            except Exception as e:
                logger.error("Error checking escalations", error=str(e))
            
            await asyncio.sleep(300)  # Check every 5 minutes

    async def inject_test_log(self, message: str, level: str = "ERROR", source: str = "test"):
        """Inject a test log entry for demonstration."""
        db = next(get_db())
        try:
            log_entry = LogEntry(
                message=message,
                level=level,
                source=source,
                log_metadata={"test": True}
            )
            db.add(log_entry)
            db.commit()
            
            logger.info("Test log injected", message=message)
            
        finally:
            db.close()
