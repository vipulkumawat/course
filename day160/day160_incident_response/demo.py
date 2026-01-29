"""Demo script for incident response system"""
import asyncio
import httpx
from datetime import datetime


async def run_demo():
    """Run automated demo scenarios"""
    base_url = "http://localhost:8000"
    
    print("\n🎬 Day 160: Automated Incident Response Demo")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Check system health
        print("\n1️⃣  Checking system health...")
        health = await client.get(f"{base_url}/health")
        print(f"   Status: {health.json()['status']}")
        
        # Get initial metrics
        print("\n2️⃣  Getting initial metrics...")
        metrics = await client.get(f"{base_url}/api/metrics")
        print(f"   {metrics.json()}")
        
        # Simulate brute force attack
        print("\n3️⃣  Simulating brute force attack...")
        event1 = await client.post(f"{base_url}/api/events", json={
            'event_type': 'brute_force_attack',
            'severity': 'high',
            'source': '192.168.1.100',
            'details': {
                'source_ip': '192.168.1.100',
                'target_user': 'admin',
                'failed_attempts': 15
            }
        })
        print(f"   Event submitted: {event1.json()['event_id']}")
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Simulate malware detection
        print("\n4️⃣  Simulating malware detection...")
        event2 = await client.post(f"{base_url}/api/events", json={
            'event_type': 'malware_detected',
            'severity': 'critical',
            'source': 'workstation-42',
            'details': {
                'system_id': 'workstation-42',
                'user_id': 'jsmith',
                'malware_type': 'ransomware'
            }
        })
        print(f"   Event submitted: {event2.json()['event_id']}")
        
        await asyncio.sleep(4)
        
        # Check responses
        print("\n5️⃣  Checking incident responses...")
        responses = await client.get(f"{base_url}/api/responses?limit=5")
        resp_data = responses.json()
        for resp in resp_data['responses']:
            print(f"   {resp['event_type']}: {len(resp['playbooks'])} playbooks executed")
        
        # Get audit log
        print("\n6️⃣  Retrieving audit log...")
        audit = await client.get(f"{base_url}/api/audit-log?limit=10")
        audit_data = audit.json()
        print(f"   Total audit entries: {len(audit_data['audit_log'])}")
        for entry in audit_data['audit_log'][:5]:
            print(f"   - {entry['action']} ({entry['status']})")
        
        # Final metrics
        print("\n7️⃣  Final metrics...")
        final_metrics = await client.get(f"{base_url}/api/metrics")
        print(f"   {final_metrics.json()}")
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("\n📊 View real-time dashboard at: http://localhost:8000")
        print("📖 API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(run_demo())
