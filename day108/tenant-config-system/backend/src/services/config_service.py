import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import jsonschema
from models.tenant_config import ConfigEntry, TenantConfigSchema, ConfigScope, ConfigState, ConfigChange
import structlog
import asyncio

logger = structlog.get_logger()

class ConfigurationService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = None
        self.redis_url = redis_url
        self.schema_cache: Dict[str, dict] = {}
        self.config_cache: Dict[str, Dict[str, Any]] = {}
        self.subscribers: Dict[str, List[callable]] = {}
        
    async def initialize(self):
        """Initialize Redis connection and load schemas"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        await self._load_config_schemas()
        logger.info("Configuration service initialized")
        
    async def _load_config_schemas(self):
        """Load configuration schemas from Redis or use defaults"""
        tenant_schema = TenantConfigSchema().model_json_schema()
        self.schema_cache['tenant'] = tenant_schema
        
        # Store schema in Redis for validation
        await self.redis_client.set(
            "config:schema:tenant", 
            json.dumps(tenant_schema),
            ex=3600  # Cache for 1 hour
        )

    async def get_tenant_config(self, tenant_id: str, config_key: Optional[str] = None) -> Dict[str, Any]:
        """Get tenant configuration with inheritance resolution"""
        cache_key = f"tenant_config:{tenant_id}"
        
        # Check cache first
        if cache_key in self.config_cache:
            config = self.config_cache[cache_key]
            if config.get('_cached_at', 0) > datetime.utcnow().timestamp() - 300:  # 5-minute cache
                return config if not config_key else config.get(config_key)
        
        # Load from Redis with inheritance
        config = await self._resolve_config_inheritance(tenant_id)
        
        # Cache result
        config['_cached_at'] = datetime.utcnow().timestamp()
        self.config_cache[cache_key] = config
        
        return config if not config_key else config.get(config_key)
    
    async def _resolve_config_inheritance(self, tenant_id: str) -> Dict[str, Any]:
        """Resolve configuration with inheritance: tenant > global defaults"""
        # Start with global defaults
        defaults = TenantConfigSchema().model_dump()
        
        # Load tenant-specific overrides
        tenant_key = f"config:tenant:{tenant_id}"
        tenant_config_raw = await self.redis_client.get(tenant_key)
        
        if tenant_config_raw:
            tenant_config = json.loads(tenant_config_raw)
            # Merge tenant config over defaults
            for key, value in tenant_config.items():
                if key.startswith('_'):  # Skip internal fields
                    continue
                defaults[key] = value
                
        return defaults
    
    async def update_tenant_config(self, tenant_id: str, updates: Dict[str, Any], updated_by: str) -> bool:
        """Update tenant configuration with validation"""
        try:
            # Get current config
            current_config = await self.get_tenant_config(tenant_id)
            
            # Apply updates
            new_config = current_config.copy()
            new_config.update(updates)
            
            # Remove internal fields for validation
            validation_config = {k: v for k, v in new_config.items() if not k.startswith('_')}
            
            # Validate against schema
            jsonschema.validate(validation_config, self.schema_cache['tenant'])
            
            # Store changes for audit trail
            changes = []
            for key, new_value in updates.items():
                old_value = current_config.get(key)
                if old_value != new_value:
                    change = ConfigChange(
                        tenant_id=tenant_id,
                        config_key=key,
                        old_value=old_value,
                        new_value=new_value,
                        changed_by=updated_by
                    )
                    changes.append(change)
            
            # Save to Redis
            tenant_key = f"config:tenant:{tenant_id}"
            validation_config['_updated_at'] = datetime.utcnow().isoformat()
            validation_config['_updated_by'] = updated_by
            
            await self.redis_client.set(
                tenant_key, 
                json.dumps(validation_config, default=str),
                ex=86400 * 30  # 30-day expiration
            )
            
            # Store audit trail
            for change in changes:
                audit_key = f"config:audit:{tenant_id}:{datetime.utcnow().isoformat()}"
                await self.redis_client.set(
                    audit_key, 
                    change.model_dump_json(),
                    ex=86400 * 365  # Keep audit for 1 year
                )
            
            # Invalidate cache
            cache_key = f"tenant_config:{tenant_id}"
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            
            # Notify subscribers
            await self._notify_config_change(tenant_id, list(updates.keys()))
            
            logger.info("Configuration updated", tenant_id=tenant_id, updates=updates)
            return True
            
        except jsonschema.ValidationError as e:
            logger.error("Configuration validation failed", error=str(e))
            raise ValueError(f"Configuration validation failed: {e.message}")
        except Exception as e:
            logger.error("Failed to update configuration", error=str(e))
            raise
    
    async def get_config_history(self, tenant_id: str, limit: int = 10) -> List[ConfigChange]:
        """Get configuration change history for a tenant"""
        pattern = f"config:audit:{tenant_id}:*"
        keys = await self.redis_client.keys(pattern)
        keys.sort(reverse=True)  # Most recent first
        
        changes = []
        for key in keys[:limit]:
            change_data = await self.redis_client.get(key)
            if change_data:
                change = ConfigChange.parse_raw(change_data)
                changes.append(change)
        
        return changes
    
    async def subscribe_to_changes(self, tenant_id: str, callback: callable):
        """Subscribe to configuration changes for a tenant"""
        if tenant_id not in self.subscribers:
            self.subscribers[tenant_id] = []
        self.subscribers[tenant_id].append(callback)
    
    async def _notify_config_change(self, tenant_id: str, changed_keys: List[str]):
        """Notify all subscribers of configuration changes"""
        if tenant_id in self.subscribers:
            for callback in self.subscribers[tenant_id]:
                try:
                    await callback(tenant_id, changed_keys)
                except Exception as e:
                    logger.error("Failed to notify subscriber", error=str(e))
    
    async def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        try:
            jsonschema.validate(config_data, self.schema_cache['tenant'])
            return True
        except jsonschema.ValidationError:
            return False
    
    async def reset_tenant_config(self, tenant_id: str, reset_by: str) -> bool:
        """Reset tenant configuration to defaults"""
        tenant_key = f"config:tenant:{tenant_id}"
        await self.redis_client.delete(tenant_key)
        
        # Log the reset
        change = ConfigChange(
            tenant_id=tenant_id,
            config_key="ALL",
            old_value="custom_config",
            new_value="defaults",
            changed_by=reset_by,
            change_reason="Configuration reset to defaults"
        )
        
        audit_key = f"config:audit:{tenant_id}:{datetime.utcnow().isoformat()}"
        await self.redis_client.set(audit_key, change.model_dump_json(), ex=86400 * 365)
        
        # Invalidate cache
        cache_key = f"tenant_config:{tenant_id}"
        if cache_key in self.config_cache:
            del self.config_cache[cache_key]
        
        # Notify subscribers
        await self._notify_config_change(tenant_id, ["ALL"])
        
        logger.info("Configuration reset to defaults", tenant_id=tenant_id)
        return True

# Global service instance
config_service = ConfigurationService()
