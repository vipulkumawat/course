"""Tenant management service."""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from models.tenant import Tenant, TenantTier, ResourceQuota, TenantMetrics
from core.quota_engine import QuotaEngine
import logging

logger = logging.getLogger(__name__)

class TenantService:
    """Service for managing tenants and their resources."""
    
    def __init__(self, quota_engine: QuotaEngine):
        self.quota_engine = quota_engine
        self.tenants_file = "data/tenants.json"
        self._load_tenants()
    
    def _load_tenants(self):
        """Load tenants from JSON file (simplified storage)."""
        try:
            if os.path.exists(self.tenants_file):
                with open(self.tenants_file, 'r') as f:
                    tenants_data = json.load(f)
                    for tenant_data in tenants_data:
                        tenant_id = tenant_data['id']
                        quota = ResourceQuota(**tenant_data['quota'])
                        self.quota_engine.set_quota(tenant_id, quota)
            else:
                # Create default tenants
                self._create_default_tenants()
        except Exception as e:
            logger.error(f"Error loading tenants: {e}")
            self._create_default_tenants()
    
    def _create_default_tenants(self):
        """Create default tenants for demo."""
        default_tenants = [
            {
                "id": "tenant-basic",
                "name": "Basic Tier Company",
                "tier": "basic",
                "quota": {
                    "cpu_cores": 1.0,
                    "memory_mb": 512,
                    "storage_mb": 1024,
                    "requests_per_minute": 100,
                    "concurrent_connections": 10
                }
            },
            {
                "id": "tenant-premium", 
                "name": "Premium Tier Company",
                "tier": "premium",
                "quota": {
                    "cpu_cores": 2.0,
                    "memory_mb": 1024,
                    "storage_mb": 4096,
                    "requests_per_minute": 500,
                    "concurrent_connections": 50
                }
            },
            {
                "id": "tenant-enterprise",
                "name": "Enterprise Tier Company", 
                "tier": "enterprise",
                "quota": {
                    "cpu_cores": 4.0,
                    "memory_mb": 4096,
                    "storage_mb": 16384,
                    "requests_per_minute": 2000,
                    "concurrent_connections": 200
                }
            }
        ]
        
        os.makedirs(os.path.dirname(self.tenants_file), exist_ok=True)
        with open(self.tenants_file, 'w') as f:
            json.dump(default_tenants, f, indent=2)
        
        # Set quotas in engine
        for tenant_data in default_tenants:
            tenant_id = tenant_data['id']
            quota = ResourceQuota(**tenant_data['quota'])
            self.quota_engine.set_quota(tenant_id, quota)
        
        logger.info("Created default tenants")
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """Get tenant by ID."""
        try:
            with open(self.tenants_file, 'r') as f:
                tenants = json.load(f)
                for tenant in tenants:
                    if tenant['id'] == tenant_id:
                        return tenant
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {e}")
        return None
    
    def get_all_tenants(self) -> List[Dict]:
        """Get all tenants."""
        try:
            with open(self.tenants_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error getting all tenants: {e}")
            return []
    
    def get_tenant_metrics(self, tenant_id: str) -> Dict:
        """Get real-time metrics for tenant."""
        utilization = self.quota_engine.get_quota_utilization(tenant_id)
        quota = self.quota_engine.quotas.get(tenant_id)
        usage = self.quota_engine.tracker.get_usage(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "quota": quota.model_dump() if quota else {},
            "current_usage": usage.model_dump() if usage else {},
            "utilization": utilization,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def process_tenant_log(self, tenant_id: str, log_data: Dict) -> Dict:
        """Process a log entry for specific tenant."""
        try:
            # Allocate resources for processing
            await self.quota_engine.allocate_resources(tenant_id, cpu=0.1, memory=50)
            
            # Get tenant's isolated storage path
            tenant_path = self.quota_engine.get_tenant_path(tenant_id)
            
            # Process log (simplified)
            log_entry = {
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": log_data,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # Save to tenant's isolated storage
            log_file = os.path.join(tenant_path, "logs.jsonl")
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            return {"status": "success", "message": "Log processed", "tenant_id": tenant_id}
            
        except Exception as e:
            logger.error(f"Error processing log for tenant {tenant_id}: {e}")
            return {"status": "error", "message": str(e), "tenant_id": tenant_id}
