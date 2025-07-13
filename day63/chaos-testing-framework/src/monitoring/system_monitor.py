"""
Chaos Testing Framework - System Monitor
Real-time monitoring of system health during chaos experiments
"""

import asyncio
import psutil
import docker
import time
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import redis.asyncio as redis
import httpx
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    service_health: Dict[str, bool]
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertThreshold:
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "greater_than"  # greater_than, less_than, equals


class SystemMonitor:
    """
    Comprehensive monitoring system for tracking health during chaos experiments
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Use Docker Desktop socket on macOS if available, otherwise use default
        docker_socket_path = '/Users/sumedhshende/.docker/run/docker.sock'
        if os.path.exists(docker_socket_path):
            self.docker_client = docker.DockerClient(base_url=f'unix://{docker_socket_path}')
        else:
            self.docker_client = docker.from_env()
        self.redis_client = None
        self.metrics_history: List[SystemMetrics] = []
        self.alert_thresholds: List[AlertThreshold] = []
        self.monitoring_active = False
        self.monitored_services = config.get('monitored_services', [])
        
        # Setup alert thresholds from config
        self._setup_alert_thresholds()
        
    async def initialize(self):
        """Initialize connections and start monitoring"""
        try:
            # Connect to Redis for metrics storage
            redis_url = self.config.get('redis_url', 'redis://localhost:6379')
            self.redis_client = redis.from_url(redis_url)
            
            logger.info("System monitor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize system monitor: {str(e)}")
            raise
    
    def _setup_alert_thresholds(self):
        """Setup alert thresholds from configuration"""
        thresholds_config = self.config.get('alert_thresholds', {})
        
        default_thresholds = [
            AlertThreshold("cpu_usage", 70.0, 90.0),
            AlertThreshold("memory_usage", 80.0, 95.0),
            AlertThreshold("disk_usage", 85.0, 95.0),
            AlertThreshold("network_latency", 100.0, 500.0),
            AlertThreshold("log_processing_rate", 100.0, 50.0, "less_than"),
        ]
        
        # Add configured thresholds
        for threshold_config in thresholds_config:
            threshold = AlertThreshold(**threshold_config)
            self.alert_thresholds.append(threshold)
        
        # Add default thresholds if not configured
        configured_metrics = {t.metric_name for t in self.alert_thresholds}
        for default_threshold in default_thresholds:
            if default_threshold.metric_name not in configured_metrics:
                self.alert_thresholds.append(default_threshold)
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        self.monitoring_active = True
        logger.info("Starting continuous system monitoring")
        
        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._monitor_service_health()),
            asyncio.create_task(self._monitor_custom_metrics()),
            asyncio.create_task(self._process_alerts())
        ]
        
        try:
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
            await self.stop_monitoring()
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.monitoring_active = False
        logger.info("Stopping system monitoring")
        
        if self.redis_client:
            await self.redis_client.close()
    
    async def _monitor_system_metrics(self):
        """Monitor basic system metrics"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Network latency (ping localhost as baseline)
                network_latency = await self._measure_network_latency()
                
                # Service health
                service_health = await self._check_service_health()
                
                # Create metrics object
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_usage=cpu_usage,
                    memory_usage=memory.percent,
                    disk_usage=disk.percent,
                    network_latency=network_latency,
                    service_health=service_health
                )
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Add to local history (keep last 1000 entries)
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > 1000:
                    self.metrics_history.pop(0)
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system metrics: {str(e)}")
                await asyncio.sleep(5)
    
    async def _monitor_service_health(self):
        """Monitor health of specific services"""
        while self.monitoring_active:
            try:
                for service in self.monitored_services:
                    await self._check_individual_service_health(service)
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring service health: {str(e)}")
                await asyncio.sleep(10)
    
    async def _monitor_custom_metrics(self):
        """Monitor custom application metrics"""
        while self.monitoring_active:
            try:
                # Log processing rate
                log_rate = await self._get_log_processing_rate()
                
                # Message queue depth
                queue_depth = await self._get_message_queue_depth()
                
                # Error rate
                error_rate = await self._get_error_rate()
                
                custom_metrics = {
                    'log_processing_rate': log_rate,
                    'message_queue_depth': queue_depth,
                    'error_rate': error_rate,
                    'timestamp': time.time()
                }
                
                # Store custom metrics
                if self.metrics_history:
                    self.metrics_history[-1].custom_metrics.update(custom_metrics)
                
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring custom metrics: {str(e)}")
                await asyncio.sleep(15)
    
    async def _process_alerts(self):
        """Process alerts based on thresholds"""
        while self.monitoring_active:
            try:
                if not self.metrics_history:
                    await asyncio.sleep(5)
                    continue
                
                latest_metrics = self.metrics_history[-1]
                
                for threshold in self.alert_thresholds:
                    await self._check_threshold(latest_metrics, threshold)
                
                await asyncio.sleep(10)  # Check alerts every 10 seconds
                
            except Exception as e:
                logger.error(f"Error processing alerts: {str(e)}")
                await asyncio.sleep(10)
    
    async def _measure_network_latency(self) -> float:
        """Measure network latency"""
        try:
            start_time = time.time()
            # Simple HTTP request to measure latency
            async with httpx.AsyncClient() as client:
                await client.get("http://localhost:8000/health", timeout=5.0)
            return (time.time() - start_time) * 1000  # Convert to ms
        except:
            return 999.0  # High latency if unreachable
    
    async def _check_service_health(self) -> Dict[str, bool]:
        """Check health of monitored services"""
        service_health = {}
        
        try:
            # Check Docker containers
            containers = self.docker_client.containers.list()
            
            for service in self.monitored_services:
                service_healthy = False
                
                for container in containers:
                    if service in container.name and container.status == 'running':
                        service_healthy = True
                        break
                
                service_health[service] = service_healthy
                
        except Exception as e:
            logger.error(f"Error checking service health: {str(e)}")
            # Assume all services are unhealthy if we can't check
            service_health = {service: False for service in self.monitored_services}
        
        return service_health
    
    async def _check_individual_service_health(self, service: str):
        """Check health of individual service with detailed probes"""
        try:
            # HTTP health check if applicable
            health_endpoints = {
                'log-collector': 'http://localhost:8001/health',
                'message-queue': 'http://localhost:15672/api/health/checks/virtual-hosts',
                'log-processor': 'http://localhost:8002/health'
            }
            
            if service in health_endpoints:
                async with httpx.AsyncClient() as client:
                    response = await client.get(health_endpoints[service], timeout=5.0)
                    healthy = response.status_code == 200
                    
                    # Store detailed health info
                    health_info = {
                        'service': service,
                        'healthy': healthy,
                        'response_time': response.elapsed.total_seconds() * 1000,
                        'timestamp': time.time()
                    }
                    
                    if self.redis_client:
                        await self.redis_client.lpush(
                            f"health:{service}",
                            str(health_info)
                        )
                        # Keep only last 100 health checks
                        await self.redis_client.ltrim(f"health:{service}", 0, 99)
                        
        except Exception as e:
            logger.error(f"Error checking health for {service}: {str(e)}")
    
    async def _get_log_processing_rate(self) -> float:
        """Get current log processing rate"""
        try:
            # This would typically query your log processing metrics
            # For demo purposes, return a simulated value
            if self.redis_client:
                rate_data = await self.redis_client.get("metrics:log_processing_rate")
                if rate_data:
                    return float(rate_data)
            
            # Simulate processing rate based on system load
            cpu_usage = psutil.cpu_percent()
            return max(0, 1000 - (cpu_usage * 10))  # Inverse relationship with CPU
            
        except Exception as e:
            logger.error(f"Error getting log processing rate: {str(e)}")
            return 0.0
    
    async def _get_message_queue_depth(self) -> int:
        """Get current message queue depth"""
        try:
            # This would query RabbitMQ management API
            # For demo purposes, return a simulated value
            return 42  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting message queue depth: {str(e)}")
            return 0
    
    async def _get_error_rate(self) -> float:
        """Get current error rate"""
        try:
            # This would typically query error logs or metrics
            # For demo purposes, return a simulated value
            return 0.5  # 0.5% error rate
            
        except Exception as e:
            logger.error(f"Error getting error rate: {str(e)}")
            return 0.0
    
    async def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in Redis for persistence"""
        try:
            if self.redis_client:
                metrics_data = {
                    'timestamp': metrics.timestamp,
                    'cpu_usage': metrics.cpu_usage,
                    'memory_usage': metrics.memory_usage,
                    'disk_usage': metrics.disk_usage,
                    'network_latency': metrics.network_latency,
                    'service_health': metrics.service_health,
                    'custom_metrics': metrics.custom_metrics
                }
                
                await self.redis_client.lpush("metrics:system", str(metrics_data))
                # Keep only last 2000 metrics (about 3 hours at 5s intervals)
                await self.redis_client.ltrim("metrics:system", 0, 1999)
                
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
    
    async def _check_threshold(self, metrics: SystemMetrics, threshold: AlertThreshold):
        """Check if metrics violate alert thresholds"""
        try:
            metric_value = None
            
            # Get metric value
            if threshold.metric_name == "cpu_usage":
                metric_value = metrics.cpu_usage
            elif threshold.metric_name == "memory_usage":
                metric_value = metrics.memory_usage
            elif threshold.metric_name == "disk_usage":
                metric_value = metrics.disk_usage
            elif threshold.metric_name == "network_latency":
                metric_value = metrics.network_latency
            elif threshold.metric_name in metrics.custom_metrics:
                metric_value = metrics.custom_metrics[threshold.metric_name]
            
            if metric_value is None:
                return
            
            # Check thresholds
            if threshold.comparison == "greater_than":
                if metric_value > threshold.critical_threshold:
                    await self._send_alert("critical", threshold.metric_name, metric_value, threshold.critical_threshold)
                elif metric_value > threshold.warning_threshold:
                    await self._send_alert("warning", threshold.metric_name, metric_value, threshold.warning_threshold)
            elif threshold.comparison == "less_than":
                if metric_value < threshold.critical_threshold:
                    await self._send_alert("critical", threshold.metric_name, metric_value, threshold.critical_threshold)
                elif metric_value < threshold.warning_threshold:
                    await self._send_alert("warning", threshold.metric_name, metric_value, threshold.warning_threshold)
                    
        except Exception as e:
            logger.error(f"Error checking threshold for {threshold.metric_name}: {str(e)}")
    
    async def _send_alert(self, level: str, metric_name: str, current_value: float, threshold_value: float):
        """Send alert for threshold violation"""
        alert = {
            'level': level,
            'metric': metric_name,
            'current_value': current_value,
            'threshold': threshold_value,
            'timestamp': time.time(),
            'message': f"{level.upper()}: {metric_name} = {current_value:.2f} (threshold: {threshold_value:.2f})"
        }
        
        logger.warning(f"ALERT: {alert['message']}")
        
        # Store alert
        if self.redis_client:
            await self.redis_client.lpush("alerts", str(alert))
            await self.redis_client.ltrim("alerts", 0, 999)  # Keep last 1000 alerts
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """Get summary of metrics over specified duration"""
        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            'cpu_avg': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            'memory_avg': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            'network_latency_avg': sum(m.network_latency for m in recent_metrics) / len(recent_metrics),
            'metrics_count': len(recent_metrics),
            'duration_minutes': duration_minutes
        }
