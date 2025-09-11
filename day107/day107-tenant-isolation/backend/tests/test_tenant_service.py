"""Tests for tenant service."""
import pytest
import asyncio
import tempfile
import os
from core.quota_engine import QuotaEngine
from services.tenant_service import TenantService

@pytest.fixture
def tenant_service():
    """Create tenant service for testing."""
    quota_engine = QuotaEngine()
    service = TenantService(quota_engine)
    return service

class TestTenantService:
    """Test tenant service functionality."""
    
    def test_get_all_tenants(self, tenant_service):
        """Test getting all tenants."""
        tenants = tenant_service.get_all_tenants()
        assert len(tenants) >= 3  # Should have default tenants
        
        tenant_ids = [t['id'] for t in tenants]
        assert 'tenant-basic' in tenant_ids
        assert 'tenant-premium' in tenant_ids
        assert 'tenant-enterprise' in tenant_ids
    
    def test_get_specific_tenant(self, tenant_service):
        """Test getting specific tenant."""
        tenant = tenant_service.get_tenant('tenant-basic')
        assert tenant is not None
        assert tenant['id'] == 'tenant-basic'
        assert tenant['tier'] == 'basic'
    
    def test_get_tenant_metrics(self, tenant_service):
        """Test getting tenant metrics."""
        metrics = tenant_service.get_tenant_metrics('tenant-basic')
        
        assert 'tenant_id' in metrics
        assert 'quota' in metrics
        assert 'utilization' in metrics
        assert metrics['tenant_id'] == 'tenant-basic'
    
    @pytest.mark.asyncio
    async def test_process_tenant_log(self, tenant_service):
        """Test processing tenant log."""
        log_data = {
            "message": "Test log entry",
            "level": "INFO"
        }
        
        result = await tenant_service.process_tenant_log('tenant-basic', log_data)
        
        assert result['status'] == 'success'
        assert result['tenant_id'] == 'tenant-basic'
        
        # Verify log was written to tenant's isolated storage
        tenant_path = tenant_service.quota_engine.get_tenant_path('tenant-basic')
        log_file = os.path.join(tenant_path, 'logs.jsonl')
        assert os.path.exists(log_file)
