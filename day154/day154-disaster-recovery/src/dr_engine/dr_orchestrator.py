import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import structlog
import json

logger = structlog.get_logger()

class RegionStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"

class RegionRole(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    OFFLINE = "offline"

class DROrchestrator:
    def __init__(self, config: Dict):
        self.config = config
        self.regions = {}
        self.current_primary = None
        self.failover_history = []
        self.metrics = {
            'total_failovers': 0,
            'successful_failovers': 0,
            'failed_failovers': 0,
            'average_rto_seconds': 0,
            'last_rpo_seconds': 0
        }
        
    async def initialize_regions(self):
        """Initialize all configured regions"""
        logger.info("Initializing DR regions")
        
        for region_name, region_config in self.config['regions'].items():
            self.regions[region_name] = {
                'config': region_config,
                'status': RegionStatus.HEALTHY,
                'role': RegionRole(region_config['role']),
                'last_health_check': datetime.now(),
                'replication_lag_ms': 0
            }
            
            if region_config['role'] == 'primary':
                self.current_primary = region_name
                
        logger.info(f"Initialized {len(self.regions)} regions", primary=self.current_primary)
        
    async def check_region_health(self, region_name: str) -> bool:
        """Check health of a specific region"""
        region = self.regions.get(region_name)
        if not region:
            return False
            
        try:
            # Simulate health check - in production, this would be actual API call
            config = region['config']
            health_url = f"http://{config['host']}:{config['port']}/health"
            
            # For demo, simulate based on status
            is_healthy = region['status'] in [RegionStatus.HEALTHY, RegionStatus.DEGRADED]
            
            region['last_health_check'] = datetime.now()
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for {region_name}", error=str(e))
            return False
            
    async def detect_failure(self) -> Optional[str]:
        """Detect if primary region has failed"""
        if not self.current_primary:
            return None
            
        failure_threshold = self.config['health_checks']['failure_threshold']
        failures = 0
        
        for i in range(failure_threshold):
            is_healthy = await self.check_region_health(self.current_primary)
            if not is_healthy:
                failures += 1
            await asyncio.sleep(1)
            
        if failures >= failure_threshold:
            logger.warning(f"Primary region {self.current_primary} failed health checks",
                         failures=failures, threshold=failure_threshold)
            return self.current_primary
            
        return None
        
    async def execute_failover(self, failed_region: str) -> Dict:
        """Execute automated failover to secondary region"""
        failover_start = time.time()
        
        logger.info("Starting failover procedure", failed_region=failed_region)
        
        try:
            # Step 1: Stop writes to failed region
            await self._stop_writes(failed_region)
            
            # Step 2: Select failover target
            target_region = await self._select_failover_target(failed_region)
            if not target_region:
                raise Exception("No healthy failover target available")
                
            # Step 3: Validate secondary region data consistency
            validation_start = time.time()
            is_consistent = await self._validate_data_consistency(target_region)
            validation_time = time.time() - validation_start
            
            if not is_consistent:
                raise Exception("Data consistency validation failed")
                
            # Step 4: Promote secondary to primary
            await self._promote_region(target_region)
            
            # Step 5: Update routing
            await self._update_routing(target_region)
            
            # Calculate RTO
            rto_seconds = time.time() - failover_start
            
            # Update metrics
            self.metrics['total_failovers'] += 1
            self.metrics['successful_failovers'] += 1
            self.metrics['average_rto_seconds'] = (
                (self.metrics['average_rto_seconds'] * (self.metrics['total_failovers'] - 1) + rto_seconds)
                / self.metrics['total_failovers']
            )
            
            # Record failover event
            failover_event = {
                'timestamp': datetime.now().isoformat(),
                'from_region': failed_region,
                'to_region': target_region,
                'rto_seconds': rto_seconds,
                'rpo_seconds': self.regions[target_region]['replication_lag_ms'] / 1000,
                'validation_time_seconds': validation_time,
                'status': 'success'
            }
            
            self.failover_history.append(failover_event)
            
            logger.info("Failover completed successfully",
                       new_primary=target_region,
                       rto=rto_seconds,
                       rpo=failover_event['rpo_seconds'])
            
            return failover_event
            
        except Exception as e:
            self.metrics['failed_failovers'] += 1
            logger.error("Failover failed", error=str(e))
            
            # Calculate RPO from replication lag even if failover failed
            rpo_seconds = 0
            if failed_region in self.regions:
                # Try to get replication lag from any available secondary
                for region_name, region in self.regions.items():
                    if region_name != failed_region and region['role'] == RegionRole.SECONDARY:
                        rpo_seconds = region['replication_lag_ms'] / 1000
                        break
            
            failover_event = {
                'timestamp': datetime.now().isoformat(),
                'from_region': failed_region,
                'to_region': None,
                'status': 'failed',
                'error': str(e),
                'rto_seconds': time.time() - failover_start,
                'rpo_seconds': rpo_seconds
            }
            self.failover_history.append(failover_event)
            
            return failover_event
            
    async def _stop_writes(self, region: str):
        """Stop writes to failed region"""
        logger.info(f"Stopping writes to {region}")
        if region in self.regions:
            self.regions[region]['status'] = RegionStatus.FAILED
        await asyncio.sleep(0.5)  # Simulate operation
        
    async def _select_failover_target(self, failed_region: str) -> Optional[str]:
        """Select healthy region for failover"""
        # First try to find a healthy secondary
        for region_name, region in self.regions.items():
            if (region_name != failed_region and 
                region['status'] == RegionStatus.HEALTHY and
                region['role'] == RegionRole.SECONDARY):
                return region_name
        
        # If no healthy secondary, try any secondary (might be degraded but recoverable)
        for region_name, region in self.regions.items():
            if (region_name != failed_region and 
                region['status'] != RegionStatus.FAILED and
                region['role'] == RegionRole.SECONDARY):
                return region_name
        
        # If still no secondary found, check if there's an offline region that can be restored
        # This handles the case where a previous failover left a region as offline
        for region_name, region in self.regions.items():
            if (region_name != failed_region and 
                region['role'] == RegionRole.OFFLINE):
                # Restore it as a secondary
                region['role'] = RegionRole.SECONDARY
                region['status'] = RegionStatus.HEALTHY
                return region_name
                
        return None
        
    async def _validate_data_consistency(self, region: str) -> bool:
        """Validate data consistency of target region"""
        logger.info(f"Validating data consistency for {region}")
        
        # Simulate consistency check
        await asyncio.sleep(1)
        
        # Check replication lag
        region_data = self.regions[region]
        lag_ms = region_data['replication_lag_ms']
        max_lag_ms = self.config['replication']['max_lag_ms']
        
        if lag_ms > max_lag_ms:
            logger.warning(f"Replication lag too high", lag=lag_ms, max=max_lag_ms)
            return False
            
        return True
        
    async def _promote_region(self, region: str):
        """Promote region to primary"""
        logger.info(f"Promoting {region} to primary")
        
        # Demote current primary to secondary (not offline) so it can be used for future failovers
        if self.current_primary and self.current_primary in self.regions:
            old_primary = self.current_primary
            # Restore the old primary as a healthy secondary for future failovers
            self.regions[old_primary]['role'] = RegionRole.SECONDARY
            # Mark it as healthy if it was just failed (it will recover)
            if self.regions[old_primary]['status'] == RegionStatus.FAILED:
                self.regions[old_primary]['status'] = RegionStatus.HEALTHY
            
        # Promote new primary
        self.regions[region]['role'] = RegionRole.PRIMARY
        self.current_primary = region
        
        await asyncio.sleep(0.5)  # Simulate promotion
        
    async def _update_routing(self, region: str):
        """Update DNS/load balancer routing"""
        logger.info(f"Updating routing to {region}")
        await asyncio.sleep(0.5)  # Simulate routing update
        
    def get_metrics(self) -> Dict:
        """Get current DR metrics"""
        return {
            **self.metrics,
            'current_primary': self.current_primary,
            'regions': {
                name: {
                    'status': region['status'].value,
                    'role': region['role'].value,
                    'replication_lag_ms': region['replication_lag_ms']
                }
                for name, region in self.regions.items()
            },
            'recent_failovers': self.failover_history[-5:]
        }
