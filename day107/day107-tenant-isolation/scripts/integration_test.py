#!/usr/bin/env python3
"""Integration tests for tenant isolation system."""
import asyncio
import aiohttp
import json
import time

async def test_system_integration():
    """Test full system integration."""
    print("🔗 Starting integration tests...")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("1️⃣ Testing health endpoint...")
        async with session.get(f"{base_url}/health") as response:
            assert response.status == 200, "Health check failed"
            print("   ✅ Health check passed")
        
        # Test 2: Get all tenants
        print("2️⃣ Testing tenant listing...")
        async with session.get(f"{base_url}/api/tenants") as response:
            assert response.status == 200, "Tenant listing failed"
            data = await response.json()
            assert len(data['tenants']) >= 3, "Should have at least 3 default tenants"
            print(f"   ✅ Found {len(data['tenants'])} tenants")
        
        # Test 3: Get tenant metrics
        print("3️⃣ Testing tenant metrics...")
        async with session.get(f"{base_url}/api/tenants/tenant-basic/metrics") as response:
            assert response.status == 200, "Tenant metrics failed"
            data = await response.json()
            assert 'tenant_id' in data, "Metrics should include tenant_id"
            assert 'quota' in data, "Metrics should include quota"
            print("   ✅ Tenant metrics retrieved")
        
        # Test 4: Process tenant log
        print("4️⃣ Testing log processing...")
        log_data = {
            "message": "Integration test log entry",
            "level": "INFO",
            "metadata": {"test": True}
        }
        headers = {"X-Tenant-ID": "tenant-basic", "Content-Type": "application/json"}
        
        async with session.post(f"{base_url}/api/tenants/tenant-basic/logs", 
                              json=log_data, headers=headers) as response:
            assert response.status == 200, "Log processing failed"
            data = await response.json()
            assert data['status'] == 'success', "Log processing should succeed"
            print("   ✅ Log processing successful")
        
        # Test 5: Load simulation
        print("5️⃣ Testing load simulation...")
        async with session.post(f"{base_url}/api/simulate-load/tenant-basic",
                              headers=headers) as response:
            assert response.status == 200, "Load simulation failed"
            data = await response.json()
            assert 'successful_requests' in data, "Should return success count"
            print(f"   ✅ Load simulation: {data['successful_requests']}/{data['total_requests']} successful")
        
        # Test 6: Quota status
        print("6️⃣ Testing quota status...")
        async with session.get(f"{base_url}/api/quota-status") as response:
            assert response.status == 200, "Quota status failed"
            data = await response.json()
            assert 'tenant-basic' in data, "Should include basic tenant status"
            print("   ✅ Quota status retrieved")
    
    print("🎉 All integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_system_integration())
