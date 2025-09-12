import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from services.config_service import ConfigurationService
from models.tenant_config import TenantConfigSchema

@pytest.fixture
def config_service():
    service = ConfigurationService()
    service.redis_client = AsyncMock()
    service.schema_cache = {'tenant': TenantConfigSchema().model_json_schema()}
    return service

@pytest.mark.asyncio
async def test_get_tenant_config(config_service):
    """Test getting tenant configuration"""
    # Mock Redis response
    config_data = {
        "log_retention_days": 60,
        "max_log_rate_per_second": 2000,
        "alert_email": "test@tenant.com"
    }
    config_service.redis_client.get.return_value = json.dumps(config_data)
    
    result = await config_service.get_tenant_config("test-tenant")
    
    assert result["log_retention_days"] == 60
    assert result["alert_email"] == "test@tenant.com"

@pytest.mark.asyncio
async def test_update_tenant_config(config_service):
    """Test updating tenant configuration"""
    # Mock current config
    current_config = TenantConfigSchema().model_dump()
    config_service.get_tenant_config = AsyncMock(return_value=current_config)
    config_service.redis_client.set = AsyncMock(return_value=True)
    config_service.redis_client.keys = AsyncMock(return_value=[])
    
    updates = {"log_retention_days": 90}
    result = await config_service.update_tenant_config("test-tenant", updates, "admin")
    
    assert result is True
    config_service.redis_client.set.assert_called()

@pytest.mark.asyncio
async def test_config_validation(config_service):
    """Test configuration validation"""
    # Valid config
    valid_config = {
        "log_retention_days": 30,
        "max_log_rate_per_second": 1000,
        "alert_email": "valid@email.com"
    }
    
    result = await config_service.validate_config(valid_config)
    assert result is True
    
    # Invalid config
    invalid_config = {
        "log_retention_days": -1,  # Invalid: negative value
        "alert_email": "invalid-email"  # Invalid: not an email
    }
    
    result = await config_service.validate_config(invalid_config)
    assert result is False

@pytest.mark.asyncio
async def test_reset_tenant_config(config_service):
    """Test resetting tenant configuration"""
    config_service.redis_client.delete = AsyncMock(return_value=True)
    config_service.redis_client.set = AsyncMock(return_value=True)
    
    result = await config_service.reset_tenant_config("test-tenant", "admin")
    
    assert result is True
    config_service.redis_client.delete.assert_called()
