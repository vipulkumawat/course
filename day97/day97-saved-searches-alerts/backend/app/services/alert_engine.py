"""
Alert monitoring and evaluation engine
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.database import DATABASE_URL
from models.schemas import Alert, SavedSearch, Notification
from .notification_service import NotificationService

logger = logging.getLogger(__name__)

class AlertEngine:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.is_running = False
        self.evaluation_interval = 30  # seconds
        
    async def start_monitoring(self):
        """Start the alert monitoring loop"""
        self.is_running = True
        logger.info("🔔 Alert engine started")
        
        while self.is_running:
            try:
                await self._evaluate_alerts()
                await asyncio.sleep(self.evaluation_interval)
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def stop_monitoring(self):
        """Stop the alert monitoring loop"""
        self.is_running = False
        logger.info("🛑 Alert engine stopped")
    
    async def _evaluate_alerts(self):
        """Evaluate all active alerts"""
        db = self.SessionLocal()
        try:
            # Get all active alerts
            active_alerts = db.query(Alert).filter(Alert.is_active == True).all()
            
            for alert in active_alerts:
                try:
                    await self._evaluate_single_alert(alert, db)
                except Exception as e:
                    logger.error(f"Error evaluating alert {alert.name}: {e}")
        
        finally:
            db.close()
    
    async def _evaluate_single_alert(self, alert: Alert, db):
        """Evaluate a single alert against current conditions"""
        # Check cooldown period
        if self._is_in_cooldown(alert):
            return
        
        # Get the saved search associated with this alert
        saved_search = db.query(SavedSearch).filter(
            SavedSearch.id == alert.saved_search_id
        ).first()
        
        if not saved_search:
            logger.warning(f"Saved search not found for alert {alert.name}")
            return
        
        # Execute the search query and evaluate condition
        search_results = await self._execute_search_query(saved_search)
        condition_met = await self._evaluate_condition(alert, search_results)
        
        if condition_met:
            await self._trigger_alert(alert, search_results, db)
    
    def _is_in_cooldown(self, alert: Alert) -> bool:
        """Check if alert is in cooldown period"""
        if not alert.last_triggered:
            return False
        
        cooldown_end = alert.last_triggered + timedelta(minutes=alert.cooldown_minutes)
        return datetime.utcnow() < cooldown_end
    
    async def _execute_search_query(self, saved_search: SavedSearch) -> Dict[str, Any]:
        """Execute the saved search query (mock implementation)"""
        # In a real implementation, this would execute against your log storage
        query_params = saved_search.query_params
        
        # Mock search results based on query parameters
        mock_results = await self._generate_mock_search_results(query_params)
        return mock_results
    
    async def _generate_mock_search_results(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock search results for demonstration"""
        import random
        
        # Simulate different patterns based on query
        query_text = query_params.get("query_text", "")
        
        if "ERROR" in query_text:
            # Error rate simulation
            error_count = random.randint(1, 20)
            total_logs = random.randint(100, 1000)
            error_rate = (error_count / total_logs) * 100
            
            return {
                "total_results": error_count,
                "aggregations": {
                    "error_rate": error_rate,
                    "total_logs": total_logs,
                    "time_window": "5m"
                },
                "sample_logs": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "service": "api-gateway",
                        "level": "ERROR",
                        "message": "Database connection timeout",
                        "metadata": {"request_id": f"req_{random.randint(1000, 9999)}"}
                    }
                ]
            }
        
        elif "duration" in query_text:
            # Performance monitoring simulation
            slow_queries = random.randint(0, 10)
            avg_duration = random.uniform(500, 3000)
            
            return {
                "total_results": slow_queries,
                "aggregations": {
                    "avg_duration": avg_duration,
                    "max_duration": avg_duration * 1.5,
                    "slow_query_count": slow_queries
                },
                "sample_logs": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "service": "database",
                        "level": "WARN",
                        "message": "Slow query detected",
                        "metadata": {"duration": avg_duration, "query": "SELECT * FROM logs"}
                    }
                ]
            }
        
        else:
            # Generic log volume simulation
            log_count = random.randint(50, 500)
            return {
                "total_results": log_count,
                "aggregations": {
                    "log_count": log_count,
                    "services": ["api", "database", "auth"]
                }
            }
    
    async def _evaluate_condition(self, alert: Alert, search_results: Dict[str, Any]) -> bool:
        """Evaluate if alert condition is met"""
        condition_type = alert.condition_type
        threshold_value = alert.threshold_value
        comparison_operator = alert.comparison_operator
        
        if condition_type == "threshold":
            return await self._evaluate_threshold_condition(
                alert, search_results, threshold_value, comparison_operator
            )
        elif condition_type == "pattern":
            return await self._evaluate_pattern_condition(alert, search_results)
        elif condition_type == "anomaly":
            return await self._evaluate_anomaly_condition(alert, search_results)
        
        return False
    
    async def _evaluate_threshold_condition(
        self, alert: Alert, search_results: Dict[str, Any], 
        threshold_value: str, comparison_operator: str
    ) -> bool:
        """Evaluate threshold-based conditions"""
        try:
            threshold = float(threshold_value)
            aggregations = search_results.get("aggregations", {})
            
            # Determine what metric to compare based on the alert's saved search
            saved_search = alert.saved_search
            query_text = saved_search.query_params.get("query_text", "")
            
            if "ERROR" in query_text:
                current_value = aggregations.get("error_rate", 0)
            elif "duration" in query_text:
                current_value = aggregations.get("avg_duration", 0)
            else:
                current_value = search_results.get("total_results", 0)
            
            # Apply comparison operator
            if comparison_operator == ">":
                return current_value > threshold
            elif comparison_operator == "<":
                return current_value < threshold
            elif comparison_operator == "=":
                return abs(current_value - threshold) < 0.01  # Floating point comparison
            elif comparison_operator == "!=":
                return abs(current_value - threshold) >= 0.01
            
        except (ValueError, TypeError):
            logger.error(f"Invalid threshold value for alert {alert.name}: {threshold_value}")
        
        return False
    
    async def _evaluate_pattern_condition(self, alert: Alert, search_results: Dict[str, Any]) -> bool:
        """Evaluate pattern-based conditions"""
        # Simple pattern matching - look for specific keywords in results
        sample_logs = search_results.get("sample_logs", [])
        
        # This is a simplified implementation
        pattern_keywords = ["timeout", "failed", "exception", "critical"]
        
        for log in sample_logs:
            message = log.get("message", "").lower()
            if any(keyword in message for keyword in pattern_keywords):
                return True
        
        return False
    
    async def _evaluate_anomaly_condition(self, alert: Alert, search_results: Dict[str, Any]) -> bool:
        """Evaluate anomaly-based conditions"""
        # Simple anomaly detection - compare current results to historical baseline
        current_count = search_results.get("total_results", 0)
        
        # Mock historical baseline (in real implementation, calculate from historical data)
        historical_baseline = 100
        anomaly_threshold = 2.0  # 2x standard deviation
        
        return current_count > (historical_baseline * anomaly_threshold)
    
    async def _trigger_alert(self, alert: Alert, search_results: Dict[str, Any], db):
        """Trigger an alert and send notifications"""
        try:
            # Update alert statistics
            alert.last_triggered = datetime.utcnow()
            alert.trigger_count += 1
            
            # Create notification records
            for channel in alert.notification_channels:
                notification = Notification(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    title=f"Alert: {alert.name}",
                    message=self._generate_alert_message(alert, search_results),
                    notification_type="alert",
                    channel=channel,
                    trigger_data=search_results,
                    status="pending"
                )
                
                db.add(notification)
            
            db.commit()
            
            # Send notifications
            await self.notification_service.send_alert_notifications(alert, search_results)
            
            logger.info(f"🚨 Alert triggered: {alert.name}")
            
        except Exception as e:
            logger.error(f"Error triggering alert {alert.name}: {e}")
            db.rollback()
    
    def _generate_alert_message(self, alert: Alert, search_results: Dict[str, Any]) -> str:
        """Generate human-readable alert message"""
        aggregations = search_results.get("aggregations", {})
        total_results = search_results.get("total_results", 0)
        
        message_parts = [
            f"Alert '{alert.name}' has been triggered.",
            f"Condition: {alert.condition_type} - {alert.comparison_operator} {alert.threshold_value}",
            f"Current results: {total_results} logs found"
        ]
        
        if "error_rate" in aggregations:
            message_parts.append(f"Error rate: {aggregations['error_rate']:.2f}%")
        
        if "avg_duration" in aggregations:
            message_parts.append(f"Average duration: {aggregations['avg_duration']:.2f}ms")
        
        message_parts.extend([
            f"Time window: {alert.time_window_minutes} minutes",
            f"Triggered at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ])
        
        return "\n".join(message_parts)
