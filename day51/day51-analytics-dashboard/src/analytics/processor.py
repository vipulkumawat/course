import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import redis.asyncio as redis

@dataclass
class MetricPoint:
    timestamp: datetime
    service: str
    metric_name: str
    value: float
    tags: Dict[str, str] = None

    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'service': self.service,
            'metric_name': self.metric_name,
            'value': self.value,
            'tags': self.tags or {}
        }

def simple_linregress(x, y):
    """Simple linear regression implementation without scipy"""
    n = len(x)
    if n < 2:
        return None, None, 0, 0, 0
    
    # Calculate means
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    # Calculate slope and intercept
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    
    if denominator == 0:
        return 0, y_mean, 0, 0, 0
    
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    
    # Calculate R-squared
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Calculate standard error
    std_err = np.sqrt(ss_res / (n - 2)) if n > 2 else 0
    
    return slope, intercept, r_squared, 0, std_err

class AnalyticsProcessor:
    def __init__(self, redis_url: str):
        self.redis_client = None
        self.redis_url = redis_url
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
    async def process_log_batch(self, logs: List[Dict[str, Any]]) -> List[MetricPoint]:
        """Process a batch of logs and extract metrics"""
        metrics = []
        
        for log in logs:
            try:
                # Extract common metrics
                timestamp = datetime.fromisoformat(log.get('timestamp', datetime.now().isoformat()))
                service = log.get('service', 'unknown')
                
                # Response time metric
                if 'response_time' in log:
                    metrics.append(MetricPoint(
                        timestamp=timestamp,
                        service=service,
                        metric_name='response_time',
                        value=float(log['response_time']),
                        tags={'endpoint': log.get('endpoint', 'unknown')}
                    ))
                
                # Error rate metric
                if log.get('level') == 'ERROR':
                    metrics.append(MetricPoint(
                        timestamp=timestamp,
                        service=service,
                        metric_name='error_count',
                        value=1.0,
                        tags={'error_type': log.get('error_type', 'unknown')}
                    ))
                
                # Request count metric
                if 'method' in log:
                    metrics.append(MetricPoint(
                        timestamp=timestamp,
                        service=service,
                        metric_name='request_count',
                        value=1.0,
                        tags={'method': log['method'], 'status': str(log.get('status', 200))}
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error processing log: {e}")
                
        return metrics
    
    async def calculate_trends(self, metrics: List[MetricPoint], window_minutes: int = 5) -> Dict[str, Any]:
        """Calculate trends for metrics over specified window"""
        if not metrics:
            return {}
            
        df = pd.DataFrame([m.to_dict() for m in metrics])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        trends = {}
        
        for metric_name in df['metric_name'].unique():
            metric_data = df[df['metric_name'] == metric_name].copy()
            metric_data = metric_data.sort_values('timestamp')
            
            if len(metric_data) < 2:
                continue
                
            # Calculate trend slope using simple linear regression
            x = np.arange(len(metric_data))
            y = metric_data['value'].values
            
            if len(y) > 1:
                slope, intercept, r_squared, p_value, std_err = simple_linregress(x, y)
                
                if slope is not None:
                    trends[metric_name] = {
                        'slope': slope,
                        'r_squared': r_squared,
                        'direction': 'increasing' if slope > 0 else 'decreasing',
                        'confidence': abs(r_squared),
                        'current_value': float(y[-1]),
                        'change_rate': (y[-1] - y[0]) / len(y) if len(y) > 1 else 0
                    }
        
        return trends
    
    async def detect_anomalies(self, metrics: List[MetricPoint], threshold: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies using statistical analysis"""
        if not metrics:
            return []
            
        df = pd.DataFrame([m.to_dict() for m in metrics])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        anomalies = []
        
        for metric_name in df['metric_name'].unique():
            metric_data = df[df['metric_name'] == metric_name].copy()
            
            if len(metric_data) < 10:  # Need sufficient data
                continue
                
            values = metric_data['value'].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                continue
                
            # Z-score anomaly detection
            z_scores = np.abs((values - mean_val) / std_val)
            anomaly_indices = np.where(z_scores > threshold)[0]
            
            for idx in anomaly_indices:
                anomaly_data = metric_data.iloc[idx]
                anomalies.append({
                    'timestamp': anomaly_data['timestamp'].isoformat(),
                    'service': anomaly_data['service'],
                    'metric_name': metric_name,
                    'value': float(anomaly_data['value']),
                    'expected_range': [mean_val - threshold * std_val, mean_val + threshold * std_val],
                    'severity': 'high' if z_scores[idx] > 3 else 'medium',
                    'z_score': float(z_scores[idx])
                })
        
        return anomalies
    
    async def store_metrics(self, metrics: List[MetricPoint]):
        """Store metrics in Redis for real-time access"""
        if not self.redis_client:
            await self.initialize()
            
        pipeline = self.redis_client.pipeline()
        
        for metric in metrics:
            # Store individual metric
            key = f"metric:{metric.service}:{metric.metric_name}"
            value = json.dumps(metric.to_dict())
            
            # Use sorted set for time-series data
            score = metric.timestamp.timestamp()
            pipeline.zadd(key, {value: score})
            
            # Keep only last 24 hours
            cutoff = (datetime.now() - timedelta(hours=24)).timestamp()
            pipeline.zremrangebyscore(key, 0, cutoff)
        
        await pipeline.execute()
    
    async def get_metrics(self, service: str, metric_name: str, 
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve metrics from Redis"""
        if not self.redis_client:
            await self.initialize()
            
        key = f"metric:{service}:{metric_name}"
        
        # Default to last hour if no time range specified
        if not start_time:
            start_time = datetime.now() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.now()
            
        start_score = start_time.timestamp()
        end_score = end_time.timestamp()
        
        result = await self.redis_client.zrangebyscore(
            key, start_score, end_score, withscores=True
        )
        
        metrics = []
        for value, score in result:
            try:
                metric_data = json.loads(value)
                metrics.append(metric_data)
            except json.JSONDecodeError:
                continue
                
        return sorted(metrics, key=lambda x: x['timestamp']) 