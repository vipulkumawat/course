"""
Replication Coordinator - Manages cross-region data synchronization
"""
import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ReplicationStatus(Enum):
    SYNCED = "synced"
    SYNCING = "syncing"
    LAGGING = "lagging"
    FAILED = "failed"

@dataclass
class ReplicationMetrics:
    region_id: str
    lag_seconds: float
    last_sync_time: float
    bytes_replicated: int
    status: ReplicationStatus
    error_count: int = 0

class ConflictResolver:
    """Handles conflicts in cross-region replication"""
    
    @staticmethod
    def resolve_conflict(local_data: dict, remote_data: dict) -> dict:
        """Last-write-wins conflict resolution"""
        local_timestamp = local_data.get('timestamp', 0)
        remote_timestamp = remote_data.get('timestamp', 0)
        
        if remote_timestamp > local_timestamp:
            logger.info(f"Conflict resolved: Using remote data (newer timestamp)")
            return remote_data
        else:
            logger.info(f"Conflict resolved: Keeping local data")
            return local_data

class ReplicationCoordinator:
    """Central coordinator for cross-region replication"""
    
    def __init__(self, region_manager):
        self.region_manager = region_manager
        self.metrics: Dict[str, ReplicationMetrics] = {}
        self.running = False
        self.replication_tasks: List[asyncio.Task] = []
        self.conflict_resolver = ConflictResolver()
        self.replication_queue = asyncio.Queue()
        
    async def start(self):
        """Start replication coordination"""
        self.running = True
        logger.info("🔄 Starting replication coordinator...")
        
        # Start replication worker
        task = asyncio.create_task(self._replication_worker())
        self.replication_tasks.append(task)
        
        # Start metrics collection
        task = asyncio.create_task(self._collect_metrics())
        self.replication_tasks.append(task)
        
        logger.info("✅ Replication coordinator started")
        
    async def stop(self):
        """Stop replication coordination"""
        self.running = False
        logger.info("🛑 Stopping replication coordinator...")
        
        for task in self.replication_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        logger.info("✅ Replication coordinator stopped")
        
    def is_active(self) -> bool:
        """Check if replication is active"""
        return self.running
        
    async def replicate_data(self, data: dict, source_region: str) -> bool:
        """Queue data for replication to other regions"""
        replication_job = {
            'data': data,
            'source_region': source_region,
            'timestamp': time.time(),
            'job_id': f"repl_{int(time.time() * 1000)}"
        }
        
        await self.replication_queue.put(replication_job)
        return True
        
    async def _replication_worker(self):
        """Background worker for processing replication jobs"""
        while self.running:
            try:
                # Get replication job with timeout
                try:
                    job = await asyncio.wait_for(
                        self.replication_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                await self._process_replication_job(job)
                
            except Exception as e:
                logger.error(f"Replication worker error: {e}")
                await asyncio.sleep(1)
                
    async def _process_replication_job(self, job: dict):
        """Process a single replication job"""
        source_region = job['source_region']
        data = job['data']
        
        # Get target regions (all except source)
        target_regions = [
            region_id for region_id in self.region_manager.regions
            if region_id != source_region and self.region_manager.is_region_healthy(region_id)
        ]
        
        logger.info(f"Replicating data from {source_region} to {len(target_regions)} regions")
        
        # Replicate to all target regions in parallel
        tasks = []
        for region_id in target_regions:
            task = asyncio.create_task(
                self._replicate_to_region(data, region_id, job['job_id'])
            )
            tasks.append(task)
            
        # Wait for all replications to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update metrics based on results
        for i, result in enumerate(results):
            region_id = target_regions[i]
            if isinstance(result, Exception):
                self._update_metrics(region_id, success=False, error=str(result))
            else:
                self._update_metrics(region_id, success=True, bytes_replicated=len(json.dumps(data)))
                
    async def _replicate_to_region(self, data: dict, target_region: str, job_id: str) -> bool:
        """Replicate data to a specific region"""
        try:
            # Simulate network delay
            await asyncio.sleep(0.1)
            
            # Get region connection
            region = self.region_manager.get_region(target_region)
            if not region:
                raise Exception(f"Region {target_region} not found")
                
            # Check for conflicts
            existing_data = await self._get_existing_data(target_region, data.get('id'))
            if existing_data:
                data = self.conflict_resolver.resolve_conflict(existing_data, data)
                
            # Store data in target region
            success = await self._store_data_in_region(target_region, data)
            
            if success:
                logger.debug(f"✅ Successfully replicated to {target_region}")
                return True
            else:
                raise Exception(f"Failed to store data in {target_region}")
                
        except Exception as e:
            logger.error(f"❌ Replication to {target_region} failed: {e}")
            raise
            
    async def _get_existing_data(self, region_id: str, data_id: str) -> Optional[dict]:
        """Get existing data from region for conflict detection"""
        # Simulate data retrieval
        await asyncio.sleep(0.01)
        return None  # No existing data for simplicity
        
    async def _store_data_in_region(self, region_id: str, data: dict) -> bool:
        """Store data in target region"""
        # Simulate data storage
        await asyncio.sleep(0.05)
        
        # Add to region's data store
        region = self.region_manager.get_region(region_id)
        if region:
            region.add_replicated_data(data)
            return True
        return False
        
    def _update_metrics(self, region_id: str, success: bool, bytes_replicated: int = 0, error: str = None):
        """Update replication metrics for a region"""
        if region_id not in self.metrics:
            self.metrics[region_id] = ReplicationMetrics(
                region_id=region_id,
                lag_seconds=0.0,
                last_sync_time=time.time(),
                bytes_replicated=0,
                status=ReplicationStatus.SYNCED
            )
            
        metric = self.metrics[region_id]
        
        if success:
            metric.last_sync_time = time.time()
            metric.bytes_replicated += bytes_replicated
            metric.status = ReplicationStatus.SYNCED
            metric.lag_seconds = 0.0
        else:
            metric.error_count += 1
            metric.status = ReplicationStatus.FAILED
            
        # Calculate lag
        current_time = time.time()
        metric.lag_seconds = current_time - metric.last_sync_time
        
        # Update status based on lag
        if metric.lag_seconds > 30:
            metric.status = ReplicationStatus.LAGGING
        elif metric.lag_seconds > 10:
            metric.status = ReplicationStatus.SYNCING
            
    async def _collect_metrics(self):
        """Continuously collect and update replication metrics"""
        while self.running:
            try:
                # Update lag calculations for all regions
                current_time = time.time()
                for region_id, metric in self.metrics.items():
                    metric.lag_seconds = current_time - metric.last_sync_time
                    
                    # Update status based on lag
                    if metric.lag_seconds > 30:
                        metric.status = ReplicationStatus.LAGGING
                    elif metric.lag_seconds > 10:
                        metric.status = ReplicationStatus.SYNCING
                    else:
                        metric.status = ReplicationStatus.SYNCED
                        
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(5)
                
    def get_metrics(self) -> Dict[str, dict]:
        """Get current replication metrics"""
        return {
            region_id: asdict(metric) 
            for region_id, metric in self.metrics.items()
        }
        
    async def trigger_failover(self, failed_region: str) -> bool:
        """Trigger failover from a failed region"""
        logger.warning(f"🚨 Triggering failover from region: {failed_region}")
        
        # Mark region as failed
        if failed_region in self.metrics:
            self.metrics[failed_region].status = ReplicationStatus.FAILED
            
        # Region manager will handle the actual failover
        return await self.region_manager.handle_region_failure(failed_region)
