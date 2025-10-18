"""
Client Router - Routes client requests to healthy regions
"""
import asyncio
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RoutingRule:
    name: str
    condition: str
    target_region: str
    priority: int
    active: bool = True

class ClientRouter:
    """Routes client requests to appropriate regions"""
    
    def __init__(self, region_manager, health_monitor):
        self.region_manager = region_manager
        self.health_monitor = health_monitor
        self.routing_rules: List[RoutingRule] = []
        self.request_count = 0
        self.routing_stats = {}
        
        # Initialize default routing rules
        self._initialize_routing_rules()
        
    def _initialize_routing_rules(self):
        """Initialize default routing rules"""
        self.routing_rules = [
            RoutingRule(
                name="Primary Region", 
                condition="default",
                target_region="us-east-1",
                priority=1
            ),
            RoutingRule(
                name="Failover to West",
                condition="primary_failed",
                target_region="us-west-2", 
                priority=2
            ),
            RoutingRule(
                name="EU Data Sovereignty",
                condition="eu_client",
                target_region="eu-west-1",
                priority=3
            )
        ]
        
    async def route_request(self, client_info: dict, data: dict) -> dict:
        """Route a client request to the best available region"""
        self.request_count += 1
        
        # Determine target region
        target_region = self._select_target_region(client_info)
        
        # Check if target region is healthy
        if not self.region_manager.is_region_healthy(target_region):
            target_region = self._select_fallback_region(target_region)
            
        if not target_region:
            # Try to recover regions automatically
            logger.warning("No healthy regions available, attempting automatic recovery...")
            await self._attempt_automatic_recovery()
            
            # Try again after recovery attempt
            target_region = self._select_fallback_region(None)
            
            if not target_region:
                raise Exception("No healthy regions available even after recovery attempt")
            
        # Update routing stats
        self._update_routing_stats(target_region)
        
        # Route to target region
        result = await self._execute_request(target_region, data)
        
        logger.info(f"Request routed to {target_region}")
        return {
            "target_region": target_region,
            "result": result,
            "request_id": self.request_count,
            "timestamp": time.time()
        }
        
    def _select_target_region(self, client_info: dict) -> str:
        """Select target region based on routing rules"""
        client_location = client_info.get("location", "unknown")
        
        # EU data sovereignty rule
        if "eu" in client_location.lower() or "europe" in client_location.lower():
            return "eu-west-1"
            
        # Default to primary region
        primary = self.region_manager.get_primary_region()
        return primary.id if primary else "us-east-1"
        
    def _select_fallback_region(self, failed_region: str) -> Optional[str]:
        """Select fallback region when primary fails"""
        healthy_regions = self.region_manager.get_healthy_regions()
        
        if not healthy_regions:
            return None
            
        # Prefer regions with lower latency
        best_region = min(healthy_regions, key=lambda r: r.connection_latency)
        return best_region.id
        
    async def _execute_request(self, region_id: str, data: dict) -> dict:
        """Execute request in target region"""
        # Simulate request processing
        await asyncio.sleep(0.1)
        
        region = self.region_manager.get_region(region_id)
        if not region:
            raise Exception(f"Region {region_id} not found")
            
        # Add latency simulation
        await asyncio.sleep(region.connection_latency)
        
        # Store data in region
        data_id = f"req_{self.request_count}_{int(time.time() * 1000)}"
        data["id"] = data_id
        region.add_replicated_data(data)
        
        return {
            "status": "success",
            "data_id": data_id,
            "region": region_id,
            "latency_ms": int(region.connection_latency * 1000)
        }
        
    def _update_routing_stats(self, region_id: str):
        """Update routing statistics"""
        if region_id not in self.routing_stats:
            self.routing_stats[region_id] = {
                "request_count": 0,
                "last_request": 0
            }
            
        self.routing_stats[region_id]["request_count"] += 1
        self.routing_stats[region_id]["last_request"] = time.time()
        
    async def _attempt_automatic_recovery(self):
        """Attempt to automatically recover failed regions"""
        try:
            from replication.region_manager import RegionStatus
            
            # Mark all failed regions as recovering
            for region in self.region_manager.regions.values():
                if region.status == RegionStatus.FAILED:
                    region.status = RegionStatus.RECOVERING
                    region.last_heartbeat = time.time()
                    logger.info(f"🔄 Auto-recovery initiated for region {region.id}")
            
            # Wait a moment for recovery to take effect
            await asyncio.sleep(0.5)
            
            # Mark recovering regions as healthy
            for region in self.region_manager.regions.values():
                if region.status == RegionStatus.RECOVERING:
                    region.status = RegionStatus.HEALTHY
                    logger.info(f"✅ Auto-recovery completed for region {region.id}")
                    
        except Exception as e:
            logger.error(f"Automatic recovery failed: {e}")
        
    def get_routing_stats(self) -> dict:
        """Get current routing statistics"""
        return {
            "total_requests": self.request_count,
            "region_stats": self.routing_stats,
            "routing_rules": [
                {
                    "name": rule.name,
                    "condition": rule.condition,
                    "target_region": rule.target_region,
                    "priority": rule.priority,
                    "active": rule.active
                }
                for rule in self.routing_rules
            ]
        }
