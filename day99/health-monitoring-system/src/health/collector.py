import asyncio
import aiohttp
import json
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"

@dataclass
class ComponentHealth:
    component_id: str
    name: str
    status: HealthStatus
    last_check: datetime
    response_time: float
    metadata: Dict[str, Any]
    metrics: Dict[str, float]

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]

class HealthCollector:
    def __init__(self, config):
        self.config = config
        self.registered_components: Dict[str, Dict] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        
    async def start(self):
        """Start the health collection service"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self.running = True
        
        # Start collection tasks
        await asyncio.gather(
            self._collect_system_metrics(),
            self._collect_component_health(),
            return_exceptions=True
        )
        
    async def stop(self):
        """Stop the health collection service"""
        self.running = False
        if self.session:
            await self.session.close()
            
    def register_component(self, component_id: str, name: str, 
                          health_endpoint: str, metadata: Dict = None):
        """Register a component for health monitoring"""
        self.registered_components[component_id] = {
            "name": name,
            "health_endpoint": health_endpoint,
            "metadata": metadata or {},
            "registered_at": datetime.now(),
            "failure_count": 0
        }
        logger.info(f"Registered component: {name} ({component_id})")
        
    async def _collect_system_metrics(self):
        """Collect system-level metrics continuously"""
        while self.running:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory metrics
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                
                # Network metrics
                network = psutil.net_io_counters()
                network_io = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
                
                # Process metrics
                process_count = len(psutil.pids())
                
                # Load average (Unix/Linux only)
                try:
                    load_average = list(psutil.getloadavg())
                except AttributeError:
                    load_average = [0.0, 0.0, 0.0]
                
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_percent=disk_percent,
                    network_io=network_io,
                    process_count=process_count,
                    load_average=load_average
                )
                
                self.system_metrics.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self.system_metrics) > 1000:
                    self.system_metrics = self.system_metrics[-1000:]
                    
                logger.debug(f"Collected system metrics: CPU={cpu_percent}%, Memory={memory_percent}%")
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                
            await asyncio.sleep(self.config.health_check_interval)
            
    async def _collect_component_health(self):
        """Collect health status from registered components"""
        while self.running:
            tasks = []
            for component_id, info in self.registered_components.items():
                task = asyncio.create_task(
                    self._check_component_health(component_id, info)
                )
                tasks.append(task)
                
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
            await asyncio.sleep(self.config.health_check_interval)
            
    async def _check_component_health(self, component_id: str, info: Dict):
        """Check health of a specific component"""
        start_time = time.time()
        
        try:
            async with self.session.get(info["health_endpoint"]) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    health_data = await response.json()
                    
                    status = HealthStatus.HEALTHY
                    if health_data.get("status") == "warning":
                        status = HealthStatus.WARNING
                    elif health_data.get("status") == "critical":
                        status = HealthStatus.CRITICAL
                    
                    self.component_health[component_id] = ComponentHealth(
                        component_id=component_id,
                        name=info["name"],
                        status=status,
                        last_check=datetime.now(),
                        response_time=response_time,
                        metadata=health_data.get("metadata", {}),
                        metrics=health_data.get("metrics", {})
                    )
                    
                    # Reset failure count on success
                    info["failure_count"] = 0
                    
                else:
                    self._handle_component_failure(component_id, info, 
                                                 f"HTTP {response.status}")
                    
        except Exception as e:
            self._handle_component_failure(component_id, info, str(e))
            
    def _handle_component_failure(self, component_id: str, info: Dict, error: str):
        """Handle component health check failure"""
        info["failure_count"] += 1
        
        status = HealthStatus.UNKNOWN
        if info["failure_count"] >= self.config.max_component_failures:
            status = HealthStatus.CRITICAL
            
        self.component_health[component_id] = ComponentHealth(
            component_id=component_id,
            name=info["name"],
            status=status,
            last_check=datetime.now(),
            response_time=0.0,
            metadata={"error": error},
            metrics={}
        )
        
        logger.warning(f"Component {info['name']} failed health check: {error}")
        
    def get_overall_health_status(self) -> HealthStatus:
        """Calculate overall system health status"""
        if not self.component_health:
            return HealthStatus.UNKNOWN
            
        statuses = [comp.status for comp in self.component_health.values()]
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            return HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in statuses):
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
            
    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        latest_metrics = self.system_metrics[-1] if self.system_metrics else None
        
        # Convert system metrics to dict with proper datetime serialization
        system_metrics_dict = None
        if latest_metrics:
            system_metrics_dict = asdict(latest_metrics)
            # Convert datetime to ISO string for JSON serialization
            if 'timestamp' in system_metrics_dict and system_metrics_dict['timestamp']:
                system_metrics_dict['timestamp'] = system_metrics_dict['timestamp'].isoformat()
        
        # Convert components to dict with proper datetime serialization
        components_dict = {}
        for comp_id, comp in self.component_health.items():
            comp_dict = asdict(comp)
            # Convert datetime to ISO string for JSON serialization
            if 'last_check' in comp_dict and comp_dict['last_check']:
                comp_dict['last_check'] = comp_dict['last_check'].isoformat()
            # Convert HealthStatus enum to string for JSON serialization
            if 'status' in comp_dict and comp_dict['status']:
                comp_dict['status'] = comp_dict['status'].value
            components_dict[comp_id] = comp_dict
        
        return {
            "overall_status": self.get_overall_health_status().value,
            "timestamp": datetime.now().isoformat(),
            "system_metrics": system_metrics_dict,
            "components": components_dict,
            "component_count": len(self.registered_components),
            "healthy_components": len([
                c for c in self.component_health.values() 
                if c.status == HealthStatus.HEALTHY
            ])
        }
