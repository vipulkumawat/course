"""
Region Manager - Manages multiple regions and their health status
"""
import asyncio
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RegionStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    FAILED = "failed"
    RECOVERING = "recovering"

@dataclass
class Region:
    id: str
    name: str
    location: str
    endpoint: str
    status: RegionStatus
    last_heartbeat: float
    data_store: Dict[str, any]
    connection_latency: float = 0.0
    
    def add_replicated_data(self, data: dict):
        """Add replicated data to region's store"""
        data_id = data.get('id', f"data_{int(time.time() * 1000)}")
        self.data_store[data_id] = data

class RegionManager:
    """Manages multiple regions and their health status"""
    
    def __init__(self):
        self.regions: Dict[str, Region] = {}
        self.primary_region: Optional[str] = None
        self.running = False
        self.heartbeat_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize regions and start health monitoring"""
        logger.info("🌍 Initializing region manager...")
        
        # Initialize demo regions
        demo_regions = [
            {
                "id": "us-east-1",
                "name": "US East (Virginia)",
                "location": "Virginia, USA",
                "endpoint": "https://us-east-1.example.com"
            },
            {
                "id": "us-west-2", 
                "name": "US West (Oregon)",
                "location": "Oregon, USA",
                "endpoint": "https://us-west-2.example.com"
            },
            {
                "id": "eu-west-1",
                "name": "Europe (Ireland)",
                "location": "Dublin, Ireland", 
                "endpoint": "https://eu-west-1.example.com"
            },
            {
                "id": "ap-south-1",
                "name": "Asia Pacific (Mumbai)",
                "location": "Mumbai, India",
                "endpoint": "https://ap-south-1.example.com"
            }
        ]
        
        for region_config in demo_regions:
            region = Region(
                id=region_config["id"],
                name=region_config["name"],
                location=region_config["location"],
                endpoint=region_config["endpoint"],
                status=RegionStatus.HEALTHY,
                last_heartbeat=time.time(),
                data_store={},
                connection_latency=self._calculate_simulated_latency(region_config["location"])
            )
            self.regions[region.id] = region
            
        # Set primary region
        self.primary_region = "us-east-1"
        
        self.running = True
        
        # Start heartbeat monitoring
        self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        
        logger.info(f"✅ Initialized {len(self.regions)} regions")
        
    def _calculate_simulated_latency(self, location: str) -> float:
        """Calculate simulated network latency based on location"""
        latency_map = {
            "Virginia, USA": 0.020,      # 20ms
            "Oregon, USA": 0.065,        # 65ms  
            "Dublin, Ireland": 0.120,    # 120ms
            "Mumbai, India": 0.180       # 180ms
        }
        return latency_map.get(location, 0.100)
        
    async def cleanup(self):
        """Clean up region manager resources"""
        self.running = False
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("🧹 Region manager cleanup completed")
        
    def get_region(self, region_id: str) -> Optional[Region]:
        """Get region by ID"""
        return self.regions.get(region_id)
        
    def get_healthy_regions(self) -> List[Region]:
        """Get all healthy regions"""
        return [
            region for region in self.regions.values()
            if region.status == RegionStatus.HEALTHY
        ]
        
    def is_region_healthy(self, region_id: str) -> bool:
        """Check if a region is healthy"""
        region = self.get_region(region_id)
        return region and region.status == RegionStatus.HEALTHY
        
    def get_primary_region(self) -> Optional[Region]:
        """Get the current primary region"""
        if self.primary_region:
            return self.get_region(self.primary_region)
        return None
        
    async def handle_region_failure(self, region_id: str) -> bool:
        """Handle failure of a specific region"""
        logger.warning(f"🚨 Handling failure of region: {region_id}")
        
        region = self.get_region(region_id)
        if not region:
            return False
            
        # Mark region as failed
        region.status = RegionStatus.FAILED
        
        # If this was the primary region, elect a new one
        if self.primary_region == region_id:
            new_primary = self._elect_new_primary()
            if new_primary:
                old_primary = self.primary_region
                self.primary_region = new_primary
                logger.warning(f"🔄 Primary region changed: {old_primary} -> {new_primary}")
                return True
            else:
                logger.error("❌ No healthy regions available for primary election!")
                return False
                
        return True
        
    def _elect_new_primary(self) -> Optional[str]:
        """Elect a new primary region from healthy regions"""
        healthy_regions = self.get_healthy_regions()
        if not healthy_regions:
            return None
            
        # Choose region with lowest latency as new primary
        best_region = min(healthy_regions, key=lambda r: r.connection_latency)
        return best_region.id
        
    async def _heartbeat_monitor(self):
        """Monitor region heartbeats and update status"""
        while self.running:
            try:
                current_time = time.time()
                
                for region in self.regions.values():
                    # Simulate heartbeat with occasional failures
                    if self._simulate_heartbeat(region):
                        region.last_heartbeat = current_time
                        
                        # Recover failed regions occasionally
                        if region.status == RegionStatus.FAILED and current_time % 60 < 1:
                            region.status = RegionStatus.RECOVERING
                            logger.info(f"🔄 Region {region.id} recovering...")
                            
                        elif region.status == RegionStatus.RECOVERING:
                            region.status = RegionStatus.HEALTHY
                            logger.info(f"✅ Region {region.id} recovered")
                            
                    else:
                        # Check if region should be marked as failed
                        time_since_heartbeat = current_time - region.last_heartbeat
                        
                        if time_since_heartbeat > 30:  # 30 seconds timeout
                            if region.status == RegionStatus.HEALTHY:
                                region.status = RegionStatus.DEGRADED
                                logger.warning(f"⚠️ Region {region.id} degraded")
                                
                        if time_since_heartbeat > 60:  # 60 seconds timeout
                            if region.status != RegionStatus.FAILED:
                                region.status = RegionStatus.FAILED
                                logger.error(f"❌ Region {region.id} failed")
                                await self.handle_region_failure(region.id)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(5)
                
    def _simulate_heartbeat(self, region: Region) -> bool:
        """Simulate region heartbeat with occasional failures"""
        # 95% success rate for most regions
        import random
        
        # Simulate region-specific reliability
        reliability_map = {
            "us-east-1": 0.95,
            "us-west-2": 0.97, 
            "eu-west-1": 0.96,
            "ap-south-1": 0.94
        }
        
        reliability = reliability_map.get(region.id, 0.95)
        return random.random() < reliability
        
    def get_region_summary(self) -> dict:
        """Get summary of all regions"""
        return {
            "total_regions": len(self.regions),
            "healthy_regions": len(self.get_healthy_regions()),
            "primary_region": self.primary_region,
            "regions": {
                region.id: {
                    "name": region.name,
                    "location": region.location,
                    "status": region.status.value,
                    "last_heartbeat": region.last_heartbeat,
                    "latency_ms": int(region.connection_latency * 1000),
                    "data_count": len(region.data_store)
                }
                for region in self.regions.values()
            }
        }
