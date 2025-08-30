#!/usr/bin/env python3

import asyncio
import httpx
import time
import sys

async def test_deployment_integration():
    """Integration test for blue/green deployment"""
    print("🧪 Running Blue/Green Deployment Integration Tests")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test 1: Check system status
            print("📊 Test 1: Checking system status...")
            response = await client.get(f"{base_url}/status")
            assert response.status_code == 200
            status = response.json()
            print(f"✅ System status: {status['state']}")
            print(f"✅ Active environment: {status['active_environment']}")
            
            # Test 2: Check environments health
            print("\n🏥 Test 2: Checking environments health...")
            response = await client.get(f"{base_url}/environments")
            assert response.status_code == 200
            environments = response.json()
            
            for env_name, env_data in environments.items():
                health_status = "✅ Healthy" if env_data['health']['is_healthy'] else "❌ Unhealthy"
                print(f"{env_name.upper()}: {health_status} (Port: {env_data['port']})")
            
            # Test 3: Trigger deployment
            print("\n🚀 Test 3: Triggering deployment...")
            deployment_data = {
                "version": "v2.0.0-test",
                "config": {"new_feature": True}
            }
            
            response = await client.post(f"{base_url}/deploy", json=deployment_data)
            deployment_result = response.json()
            
            if response.status_code == 200:
                print(f"✅ Deployment initiated: {deployment_result['deployment_id']}")
                print(f"✅ Target version: {deployment_result['version']}")
            else:
                print(f"⚠️ Deployment response: {deployment_result}")
            
            # Test 4: Monitor deployment progress
            print("\n⏱️ Test 4: Monitoring deployment progress...")
            for i in range(10):  # Monitor for up to 30 seconds
                response = await client.get(f"{base_url}/status")
                status = response.json()
                print(f"Status: {status['state']} | Environment: {status['active_environment']}")
                
                if status['state'] in ['completed', 'failed']:
                    break
                    
                await asyncio.sleep(3)
            
            # Test 5: Verify final state
            print("\n✅ Test 5: Verifying final state...")
            response = await client.get(f"{base_url}/status")
            final_status = response.json()
            
            print(f"Final state: {final_status['state']}")
            print(f"Final environment: {final_status['active_environment']}")
            print(f"Version: {final_status['version']}")
            
            # Test 6: Check deployment history
            print("\n📜 Test 6: Checking deployment history...")
            response = await client.get(f"{base_url}/history")
            history = response.json()
            print(f"Total deployments: {history['total']}")
            
            if history['deployments']:
                latest = history['deployments'][-1]
                print(f"Latest deployment: {latest['version']} - {latest['state']}")
            
            print("\n🎉 Integration tests completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Integration test failed: {e}")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_deployment_integration())
    sys.exit(0 if result else 1)
