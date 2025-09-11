"""Resource quota enforcement engine."""
import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from models.tenant import TenantTier, ResourceQuota, ResourceUsage
import logging

logger = logging.getLogger(__name__)

class QuotaViolationError(Exception):
    """Raised when resource quota is exceeded."""
    pass

class ResourceTracker:
    """Tracks resource usage per tenant."""
    
    def __init__(self):
        self._usage: Dict[str, ResourceUsage] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._request_windows: Dict[str, List[float]] = {}
    
    def update_usage(self, tenant_id: str, usage: ResourceUsage) -> None:
        """Update resource usage for tenant."""
        with self._lock:
            self._usage[tenant_id] = usage
    
    def get_usage(self, tenant_id: str) -> Optional[ResourceUsage]:
        """Get current usage for tenant."""
        with self._lock:
            return self._usage.get(tenant_id)
    
    def record_request(self, tenant_id: str) -> None:
        """Record API request for rate limiting."""
        current_time = time.time()
        with self._lock:
            if tenant_id not in self._request_windows:
                self._request_windows[tenant_id] = []
            
            # Clean old requests (older than 1 minute)
            cutoff = current_time - 60
            self._request_windows[tenant_id] = [
                t for t in self._request_windows[tenant_id] if t > cutoff
            ]
            
            self._request_windows[tenant_id].append(current_time)
    
    def get_request_count(self, tenant_id: str, window_seconds: int = 60) -> int:
        """Get request count in time window."""
        current_time = time.time()
        cutoff = current_time - window_seconds
        
        with self._lock:
            requests = self._request_windows.get(tenant_id, [])
            return len([t for t in requests if t > cutoff])

class QuotaEngine:
    """Main quota enforcement engine."""
    
    def __init__(self):
        self.tracker = ResourceTracker()
        self.quotas: Dict[str, ResourceQuota] = {}
        self._monitoring_task = None
        self._isolation_paths: Dict[str, str] = {}
    
    def set_quota(self, tenant_id: str, quota: ResourceQuota) -> None:
        """Set resource quota for tenant."""
        self.quotas[tenant_id] = quota
        # Create isolation directory
        import os
        tenant_path = f"data/tenant_data/{tenant_id}"
        os.makedirs(tenant_path, exist_ok=True)
        self._isolation_paths[tenant_id] = tenant_path
        logger.info(f"Set quota for tenant {tenant_id}: {quota}")
    
    def get_tenant_path(self, tenant_id: str) -> str:
        """Get isolated filesystem path for tenant."""
        return self._isolation_paths.get(tenant_id, f"data/tenant_data/{tenant_id}")
    
    async def check_quota(self, tenant_id: str, resource_type: str, 
                         requested_amount: float = 1.0) -> bool:
        """Check if resource request is within quota."""
        if tenant_id not in self.quotas:
            raise ValueError(f"No quota defined for tenant {tenant_id}")
        
        quota = self.quotas[tenant_id]
        current_usage = self.tracker.get_usage(tenant_id)
        
        if resource_type == "cpu":
            # Check if current usage + requested amount would exceed quota
            current_cpu = current_usage.cpu_usage_percent if current_usage else 0
            if (current_cpu + requested_amount * 100) > quota.cpu_cores * 100:
                return False
        
        elif resource_type == "memory":
            # Check if current usage + requested amount would exceed quota
            current_memory = current_usage.memory_usage_mb if current_usage else 0
            if (current_memory + requested_amount) > quota.memory_mb:
                return False
        
        elif resource_type == "requests":
            request_count = self.tracker.get_request_count(tenant_id)
            if request_count >= quota.requests_per_minute:
                return False
        
        elif resource_type == "connections":
            # Check if current connections + requested amount would exceed quota
            current_connections = current_usage.concurrent_connections if current_usage else 0
            if (current_connections + requested_amount) > quota.concurrent_connections:
                return False
        
        return True
    
    async def allocate_resources(self, tenant_id: str, cpu: float = 0, 
                               memory: int = 0, connections: int = 0) -> bool:
        """Allocate resources if within quota."""
        # Check all resource types
        checks = [
            await self.check_quota(tenant_id, "cpu", cpu),
            await self.check_quota(tenant_id, "memory", memory),
            await self.check_quota(tenant_id, "connections", connections)
        ]
        
        if not all(checks):
            raise QuotaViolationError(f"Resource allocation would exceed quota for tenant {tenant_id}")
        
        # Record the allocation
        self.tracker.record_request(tenant_id)
        return True
    
    def get_quota_utilization(self, tenant_id: str) -> Dict[str, float]:
        """Get current quota utilization percentages."""
        if tenant_id not in self.quotas:
            return {}
        
        quota = self.quotas[tenant_id]
        usage = self.tracker.get_usage(tenant_id)
        request_count = self.tracker.get_request_count(tenant_id)
        
        # Calculate utilization percentages
        cpu_util = 0.0
        memory_util = 0.0
        connection_util = 0.0
        
        if usage:
            cpu_util = min(usage.cpu_usage_percent / (quota.cpu_cores * 100) * 100, 100)
            memory_util = min(usage.memory_usage_mb / quota.memory_mb * 100, 100)
            connection_util = min(usage.concurrent_connections / quota.concurrent_connections * 100, 100)
        
        # Requests utilization can be calculated even without usage data
        request_util = min(request_count / quota.requests_per_minute * 100, 100)
        
        return {
            "cpu": cpu_util,
            "memory": memory_util,
            "requests": request_util,
            "connections": connection_util
        }
    
    async def start_monitoring(self):
        """Start background resource monitoring."""
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
    
    async def _monitor_resources(self):
        """Background task to monitor system resources."""
        while True:
            try:
                # Get system-wide metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Update usage for all tenants (simplified - in real system would track per-process)
                for tenant_id in self.quotas.keys():
                    # Simulate per-tenant resource usage
                    tenant_usage = ResourceUsage(
                        tenant_id=tenant_id,
                        cpu_usage_percent=cpu_percent / len(self.quotas) if self.quotas else 0,
                        memory_usage_mb=int(memory.used / 1024 / 1024 / len(self.quotas)) if self.quotas else 0,
                        storage_usage_mb=100,  # Simplified
                        active_requests=self.tracker.get_request_count(tenant_id, 60),
                        concurrent_connections=1  # Simplified
                    )
                    self.tracker.update_usage(tenant_id, tenant_usage)
                
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(5)
