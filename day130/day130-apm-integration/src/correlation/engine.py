import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import structlog
import redis.asyncio as redis

logger = structlog.get_logger()

@dataclass
class EnrichedLog:
    original_log: Dict[str, Any]
    metrics_context: Dict[str, Any]
    correlation_id: str
    enhancement_level: str
    timestamp: float

class CorrelationEngine:
    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.config = config
        self.correlation_windows = {}
        self.alert_thresholds = config.get('alerts', {})
        
    async def process_log_entry(self, log_entry: Dict[str, Any]) -> EnrichedLog:
        """Process a log entry and enrich with performance context"""
        timestamp = log_entry.get('timestamp', time.time())
        
        # Get current metrics context
        metrics_context = await self._get_metrics_context(timestamp)
        
        # Determine enhancement level
        enhancement_level = self._calculate_enhancement_level(metrics_context, log_entry)
        
        # Create correlation ID
        correlation_id = f"corr_{int(timestamp)}_{hash(str(log_entry))}"
        
        enriched_log = EnrichedLog(
            original_log=log_entry,
            metrics_context=metrics_context,
            correlation_id=correlation_id,
            enhancement_level=enhancement_level,
            timestamp=timestamp
        )
        
        # Store enriched log
        await self._store_enriched_log(enriched_log)
        
        # Check for alert conditions
        await self._check_alert_conditions(enriched_log)
        
        return enriched_log
    
    async def _get_metrics_context(self, timestamp: float) -> Dict[str, Any]:
        """Get metrics context for the given timestamp"""
        window_start = int(timestamp - 30)  # 30-second window
        window_end = int(timestamp)
        
        metrics_data = {}
        
        # Collect system metrics from the time window
        for ts in range(window_start, window_end + 1):
            key = f"metrics:{ts}"
            data = await self.redis_client.hgetall(key)
            if data:
                for field, value in data.items():
                    # Decode bytes keys and values if needed
                    field_str = field.decode() if isinstance(field, bytes) else field
                    value_str = value.decode() if isinstance(value, bytes) else value
                    if field_str != 'timestamp':
                        metrics_data.setdefault(field_str, []).append(float(value_str))
        
        # Calculate aggregated metrics
        context = {}
        for metric, values in metrics_data.items():
            if values:
                context[f"{metric}_avg"] = sum(values) / len(values)
                context[f"{metric}_max"] = max(values)
                context[f"{metric}_min"] = min(values)
        
        return context
    
    def _calculate_enhancement_level(self, metrics_context: Dict[str, Any], log_entry: Dict[str, Any]) -> str:
        """Calculate how much to enhance the log based on metrics and log content"""
        cpu_avg = metrics_context.get('cpu_avg', 0)
        memory_avg = metrics_context.get('memory_avg', 0)
        
        log_level = log_entry.get('level', '').upper()
        
        # Critical enhancement for errors during high resource usage
        if log_level == 'ERROR' and (cpu_avg > 80 or memory_avg > 75):
            return 'CRITICAL'
        
        # High enhancement for warnings during moderate resource usage
        if log_level in ['ERROR', 'WARNING'] and (cpu_avg > 60 or memory_avg > 60):
            return 'HIGH'
        
        # Normal enhancement for all other cases
        return 'NORMAL'
    
    async def _store_enriched_log(self, enriched_log: EnrichedLog):
        """Store enriched log in Redis"""
        key = f"enriched_logs:{enriched_log.correlation_id}"
        data = json.dumps(asdict(enriched_log), default=str)
        
        await self.redis_client.set(key, data, ex=86400)  # 24-hour expiry
        
        # Also add to a time-ordered list for querying
        list_key = f"logs_timeline:{int(enriched_log.timestamp // 3600)}"  # Hourly buckets
        await self.redis_client.lpush(list_key, enriched_log.correlation_id)
        await self.redis_client.expire(list_key, 86400)
    
    async def _check_alert_conditions(self, enriched_log: EnrichedLog):
        """Check if alert conditions are met"""
        metrics = enriched_log.metrics_context
        cpu_avg = metrics.get('cpu_avg', 0)
        memory_avg = metrics.get('memory_avg', 0)
        
        alerts = []
        
        if cpu_avg > self.alert_thresholds.get('cpu_critical', 90):
            alerts.append({
                'type': 'CPU_CRITICAL',
                'value': cpu_avg,
                'threshold': self.alert_thresholds['cpu_critical'],
                'correlation_id': enriched_log.correlation_id
            })
            
        if memory_avg > self.alert_thresholds.get('memory_critical', 85):
            alerts.append({
                'type': 'MEMORY_CRITICAL', 
                'value': memory_avg,
                'threshold': self.alert_thresholds['memory_critical'],
                'correlation_id': enriched_log.correlation_id
            })
        
        # Store alerts
        for alert in alerts:
            alert_timestamp = int(time.time())
            alert['timestamp'] = alert_timestamp  # Ensure timestamp is in alert data
            alert_key = f"alerts:{alert_timestamp}"
            await self.redis_client.set(alert_key, json.dumps(alert), ex=3600)
            logger.warning("APM Alert generated", alert=alert)
    
    async def get_recent_logs(self, hours: int = 1) -> List[EnrichedLog]:
        """Get recent enriched logs"""
        current_hour = int(time.time() // 3600)
        logs = []
        
        # Check current hour and previous hours (inclusive)
        for hour_offset in range(hours + 1):  # +1 to include current hour
            list_key = f"logs_timeline:{current_hour - hour_offset}"
            correlation_ids = await self.redis_client.lrange(list_key, 0, -1)
            
            for correlation_id in correlation_ids:
                # Handle both bytes and string correlation_ids
                corr_id = correlation_id.decode() if isinstance(correlation_id, bytes) else correlation_id
                key = f"enriched_logs:{corr_id}"
                data = await self.redis_client.get(key)
                if data:
                    try:
                        log_data = json.loads(data)
                        logs.append(EnrichedLog(**log_data))
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error("Error parsing log data", error=str(e), key=key)
                        continue
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)
