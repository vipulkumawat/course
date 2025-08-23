import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..models.log_models import LogEntry, TimeSeriesData, ChartDataPoint, HeatmapData, DashboardMetrics
import structlog
import random

logger = structlog.get_logger()

class DemoDataService:
    def __init__(self):
        self.logs = []
        self.load_demo_data()
    
    def load_demo_data(self):
        """Load demo data from the generated JSON file"""
        try:
            # Path to demo data relative to backend directory
            demo_data_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts', 'demo_logs.json')
            if os.path.exists(demo_data_path):
                with open(demo_data_path, 'r') as f:
                    raw_logs = json.load(f)
                
                # Convert raw logs to LogEntry objects
                for raw_log in raw_logs:
                    log_entry = LogEntry(
                        id=len(self.logs) + 1,
                        timestamp=datetime.fromisoformat(raw_log['timestamp']),
                        service=raw_log['service'],
                        level=raw_log['level'],
                        message=raw_log['message'],
                        response_time=raw_log['response_time'],
                        status_code=raw_log['status_code'],
                        endpoint=raw_log['endpoint'],
                        user_id=raw_log['user_id']
                    )
                    self.logs.append(log_entry)
                
                logger.info(f"Loaded {len(self.logs)} demo log entries")
            else:
                logger.warning(f"Demo data file not found at {demo_data_path}")
                # Generate some fallback data
                self.generate_fallback_data()
        except Exception as e:
            logger.error(f"Error loading demo data: {e}")
            self.generate_fallback_data()
    
    def generate_fallback_data(self):
        """Generate fallback demo data if file loading fails"""
        services = ['api-gateway', 'user-service', 'payment-service']
        levels = ['INFO', 'WARN', 'ERROR']
        
        for i in range(100):
            log_entry = LogEntry(
                id=i + 1,
                timestamp=datetime.now() - timedelta(hours=random.randint(0, 24)),
                service=random.choice(services),
                level=random.choice(levels),
                message=f"Fallback log entry {i + 1}",
                response_time=random.uniform(50, 300),
                status_code=random.choice([200, 400, 500]),
                endpoint=f"/api/endpoint/{i}",
                user_id=f"user-{i}"
            )
            self.logs.append(log_entry)
    
    def get_logs_in_timeframe(self, hours: int = 24) -> List[LogEntry]:
        """Get logs within the specified time frame"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        return [
            log for log in self.logs 
            if start_time <= log.timestamp <= end_time
        ]
    
    def get_logs_by_service(self, services: Optional[List[str]] = None) -> List[LogEntry]:
        """Get logs filtered by service"""
        if not services:
            return self.logs
        
        return [log for log in self.logs if log.service in services]
    
    def get_error_logs(self, hours: int = 24) -> List[LogEntry]:
        """Get error logs within the specified time frame"""
        logs = self.get_logs_in_timeframe(hours)
        return [log for log in logs if log.level == 'ERROR']
    
    def get_service_performance(self, hours: int = 1) -> Dict[str, Any]:
        """Get service performance metrics"""
        logs = self.get_logs_in_timeframe(hours)
        
        service_stats = {}
        for log in logs:
            if log.service not in service_stats:
                service_stats[log.service] = {
                    'total_logs': 0,
                    'error_count': 0,
                    'total_response_time': 0,
                    'avg_response_time': 0
                }
            
            service_stats[log.service]['total_logs'] += 1
            if log.level == 'ERROR':
                service_stats[log.service]['error_count'] += 1
            if log.response_time:
                service_stats[log.service]['total_response_time'] += log.response_time
        
        # Calculate averages
        for service in service_stats:
            if service_stats[service]['total_logs'] > 0:
                service_stats[service]['avg_response_time'] = (
                    service_stats[service]['total_response_time'] / 
                    service_stats[service]['total_logs']
                )
        
        return service_stats
    
    def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get current dashboard metrics"""
        logs_24h = self.get_logs_in_timeframe(24)
        error_logs = [log for log in logs_24h if log.level == 'ERROR']
        
        total_logs = len(logs_24h)
        error_rate = (len(error_logs) / total_logs * 100) if total_logs > 0 else 0
        
        response_times = [log.response_time for log in logs_24h if log.response_time]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        active_services = len(set(log.service for log in logs_24h))
        
        return DashboardMetrics(
            total_logs=total_logs,
            error_rate=round(error_rate, 2),
            avg_response_time=round(avg_response_time, 2),
            active_services=active_services,
            timestamp=datetime.now()
        )
