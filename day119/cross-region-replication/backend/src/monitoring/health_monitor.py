"""
Health Monitor - Comprehensive system health monitoring
"""
import asyncio
import time
import psutil
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitors system and region health"""
    
    def __init__(self, region_manager):
        self.region_manager = region_manager
        self.running = False
        self.monitoring_task: asyncio.Task = None
        self.metrics = {
            "system": {},
            "replication": {},
            "alerts": []
        }
        
    async def start_monitoring(self):
        """Start health monitoring"""
        self.running = True
        logger.info("💓 Starting health monitor...")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ Health monitor started")
        
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Health monitor stopped")
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.metrics["system"] = system_metrics
                
                # Collect region health
                region_health = self._collect_region_health()
                self.metrics["regions"] = region_health
                
                # Check for alerts
                await self._check_alerts()
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(10)
                
    def _collect_system_metrics(self) -> dict:
        """Collect system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": time.time(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
            return {}
            
    def _collect_region_health(self) -> dict:
        """Collect region health metrics"""
        region_summary = self.region_manager.get_region_summary()
        
        # Add health scores
        for region_id, region_data in region_summary["regions"].items():
            region = self.region_manager.get_region(region_id)
            if region:
                health_score = self._calculate_health_score(region)
                region_data["health_score"] = health_score
                
        return region_summary
        
    def _calculate_health_score(self, region) -> float:
        """Calculate health score for a region (0-100)"""
        base_score = 100.0
        
        # Deduct points based on status
        status_penalties = {
            "healthy": 0,
            "degraded": 20,
            "failed": 80,
            "recovering": 40
        }
        
        base_score -= status_penalties.get(region.status.value, 0)
        
        # Deduct points for high latency
        if region.connection_latency > 0.2:  # 200ms
            base_score -= 10
        elif region.connection_latency > 0.1:  # 100ms
            base_score -= 5
            
        # Deduct points for old heartbeat
        time_since_heartbeat = time.time() - region.last_heartbeat
        if time_since_heartbeat > 30:
            base_score -= 20
        elif time_since_heartbeat > 10:
            base_score -= 10
            
        return max(0.0, base_score)
        
    async def _check_alerts(self):
        """Check for alert conditions"""
        current_alerts = []
        
        # Check system alerts
        system_metrics = self.metrics.get("system", {})
        if system_metrics.get("cpu_percent", 0) > 80:
            current_alerts.append({
                "type": "system",
                "severity": "warning",
                "message": f"High CPU usage: {system_metrics['cpu_percent']:.1f}%",
                "timestamp": time.time()
            })
            
        if system_metrics.get("memory_percent", 0) > 85:
            current_alerts.append({
                "type": "system", 
                "severity": "warning",
                "message": f"High memory usage: {system_metrics['memory_percent']:.1f}%",
                "timestamp": time.time()
            })
            
        # Check region alerts
        regions = self.metrics.get("regions", {}).get("regions", {})
        healthy_count = sum(1 for r in regions.values() if r["status"] == "healthy")
        total_count = len(regions)
        
        if healthy_count < total_count * 0.5:  # Less than 50% healthy
            current_alerts.append({
                "type": "region",
                "severity": "critical",
                "message": f"Only {healthy_count}/{total_count} regions healthy",
                "timestamp": time.time()
            })
        elif healthy_count < total_count * 0.75:  # Less than 75% healthy
            current_alerts.append({
                "type": "region",
                "severity": "warning", 
                "message": f"Region health degraded: {healthy_count}/{total_count} healthy",
                "timestamp": time.time()
            })
            
        # Update alerts (keep only recent ones)
        current_time = time.time()
        self.metrics["alerts"] = [
            alert for alert in current_alerts
            if current_time - alert["timestamp"] < 300  # 5 minutes
        ] + [
            alert for alert in self.metrics.get("alerts", [])
            if current_time - alert["timestamp"] < 300
        ]
        
    async def get_comprehensive_status(self) -> dict:
        """Get comprehensive system status"""
        return {
            "timestamp": time.time(),
            "system": self.metrics.get("system", {}),
            "regions": self.metrics.get("regions", {}),
            "alerts": self.metrics.get("alerts", []),
            "overall_status": self._get_overall_status()
        }
        
    def _get_overall_status(self) -> str:
        """Get overall system status"""
        alerts = self.metrics.get("alerts", [])
        
        if any(alert["severity"] == "critical" for alert in alerts):
            return "critical"
        elif any(alert["severity"] == "warning" for alert in alerts):
            return "warning" 
        else:
            return "healthy"
