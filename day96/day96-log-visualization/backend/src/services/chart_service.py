import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..models.log_models import LogEntry, TimeSeriesData, ChartDataPoint, HeatmapData, DashboardMetrics
from .demo_data_service import DemoDataService
import structlog

logger = structlog.get_logger()

class ChartDataService:
    def __init__(self, db_session=None):
        # Use demo data service instead of database
        self.demo_service = DemoDataService()
    
    async def get_error_rate_trends(self, 
                                   hours: int = 24, 
                                   services: Optional[List[str]] = None) -> List[TimeSeriesData]:
        """Generate error rate trends for specified time period and services"""
        # Get logs from demo service
        logs = self.demo_service.get_logs_in_timeframe(hours)
        if services:
            logs = [log for log in logs if log.service in services]
        
        # Group by service and hour
        from collections import defaultdict
        service_hour_data = defaultdict(lambda: defaultdict(lambda: {'total': 0, 'errors': 0}))
        
        for log in logs:
            hour = log.timestamp.replace(minute=0, second=0, microsecond=0)
            service_hour_data[log.service][hour]['total'] += 1
            if log.level == 'ERROR':
                service_hour_data[log.service][hour]['errors'] += 1
        
        # Process results into time series
        chart_series = []
        colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
        
        for i, (service, hour_data) in enumerate(service_hour_data.items()):
            data_points = []
            for hour, stats in hour_data.items():
                error_rate = (stats['errors'] / stats['total'] * 100) if stats['total'] > 0 else 0
                data_points.append(
                    ChartDataPoint(
                        timestamp=hour,
                        value=error_rate,
                        metadata={'total_logs': stats['total'], 'error_count': stats['errors']}
                    )
                )
            
            if data_points:
                chart_series.append(
                    TimeSeriesData(
                        series_name=f"{service} Error Rate",
                        data_points=sorted(data_points, key=lambda x: x.timestamp),
                        chart_type="line",
                        color=colors[i % len(colors)]
                    )
                )
        
        return chart_series
    
    async def get_response_time_heatmap(self, 
                                      hours: int = 24) -> HeatmapData:
        """Generate response time heatmap by service and time"""
        # Get logs from demo service
        logs = self.demo_service.get_logs_in_timeframe(hours)
        logs = [log for log in logs if log.response_time]
        
        # Group by service and hour
        from collections import defaultdict
        service_hour_data = defaultdict(lambda: defaultdict(list))
        
        for log in logs:
            hour = log.timestamp.hour
            service_hour_data[log.service][hour].append(log.response_time)
        
        # Prepare heatmap data structure
        services = list(service_hour_data.keys())
        hours_list = list(range(24))
        
        # Initialize matrix with zeros
        values = [[0.0 for _ in hours_list] for _ in services]
        
        # Fill matrix with actual data
        for service_idx, service in enumerate(services):
            for hour_idx, hour in enumerate(hours_list):
                if hour in service_hour_data[service]:
                    avg_response_time = sum(service_hour_data[service][hour]) / len(service_hour_data[service][hour])
                    values[service_idx][hour_idx] = round(avg_response_time, 2)
        
        return HeatmapData(
            x_labels=[f"{h:02d}:00" for h in hours_list],
            y_labels=services,
            values=values
        )
    
    async def get_service_performance_bars(self, 
                                         hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent service performance for bar charts"""
        # Get service performance from demo service
        service_stats = self.demo_service.get_service_performance(hours)
        
        chart_data = []
        for service, stats in service_stats.items():
            error_rate = (stats['error_count'] / stats['total_logs'] * 100) if stats['total_logs'] > 0 else 0
            chart_data.append({
                'service': service,
                'requests': stats['total_logs'],
                'avg_response_time': round(stats['avg_response_time'], 2),
                'error_rate': round(error_rate, 2)
            })
        
        return sorted(chart_data, key=lambda x: x['requests'], reverse=True)
    
    async def get_real_time_metrics(self) -> DashboardMetrics:
        """Get current dashboard metrics"""
        # Get metrics from demo service
        return self.demo_service.get_dashboard_metrics()
