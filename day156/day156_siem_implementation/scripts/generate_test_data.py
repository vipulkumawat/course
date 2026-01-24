"""
Generate realistic security events for testing
"""
import asyncio
import aiohttp
import random
import time
from datetime import datetime

API_URL = "http://localhost:8000/api/events/ingest"

# Test users and IPs
USERS = ['alice', 'bob', 'charlie', 'admin', 'service_account']
SUSPICIOUS_IPS = ['192.168.1.100', '10.0.0.50', '172.16.0.20']
NORMAL_IPS = ['192.168.1.10', '192.168.1.11', '192.168.1.12']
CRITICAL_RESOURCES = ['/admin/users', '/api/database', '/config/secrets']
NORMAL_RESOURCES = ['/api/products', '/api/orders', '/dashboard']


async def send_event(session, event_data):
    """Send event to SIEM API"""
    try:
        async with session.post(API_URL, json=event_data) as response:
            result = await response.json()
            if result.get('incident_created'):
                print(f"🚨 INCIDENT CREATED: {result.get('incident_id')}")
            return result
    except Exception as e:
        print(f"Error sending event: {e}")


async def generate_normal_activity(session):
    """Generate normal user activity"""
    user = random.choice(USERS[:3])  # Normal users
    ip = random.choice(NORMAL_IPS)
    resource = random.choice(NORMAL_RESOURCES)
    
    event = {
        'type': 'access',
        'timestamp': time.time(),
        'user': user,
        'client_ip': ip,
        'resource_path': resource,
        'action': 'read',
        'status_code': 200,
        'bytes': random.randint(100, 10000)
    }
    
    await send_event(session, event)
    print(f"✅ Normal activity: {user} accessed {resource}")


async def simulate_brute_force_attack(session):
    """Simulate brute force authentication attack"""
    attacker_ip = random.choice(SUSPICIOUS_IPS)
    target_user = random.choice(USERS)
    
    print(f"\n🔴 Simulating brute force attack on {target_user} from {attacker_ip}")
    
    # Send multiple failed login attempts
    for i in range(7):
        event = {
            'type': 'auth',
            'timestamp': time.time(),
            'username': target_user,
            'source_ip': attacker_ip,
            'success': False,
            'auth_method': 'password',
            'service': 'ssh'
        }
        await send_event(session, event)
        print(f"  ❌ Failed login attempt {i + 1}")
        await asyncio.sleep(0.5)
    
    # Optional: successful login after brute force
    if random.random() < 0.3:
        event = {
            'type': 'auth',
            'timestamp': time.time(),
            'username': target_user,
            'source_ip': attacker_ip,
            'success': True,
            'auth_method': 'password',
            'service': 'ssh'
        }
        await send_event(session, event)
        print(f"  ⚠️  SUCCESSFUL LOGIN after brute force!")


async def simulate_privilege_escalation(session):
    """Simulate privilege escalation attempt"""
    user = random.choice(USERS[:3])
    ip = random.choice(NORMAL_IPS)
    
    print(f"\n🟠 Simulating privilege escalation by {user}")
    
    # Multiple privilege escalation actions
    actions = ['sudo /bin/bash', 'su root', 'sudo vim /etc/passwd']
    
    for action in actions:
        event = {
            'type': 'admin',
            'timestamp': time.time(),
            'user': user,
            'source_ip': ip,
            'action': action,
            'command': action,
            'success': True
        }
        await send_event(session, event)
        print(f"  🔓 Privilege action: {action}")
        await asyncio.sleep(1)


async def simulate_anomalous_access(session):
    """Simulate access from new/unusual location"""
    user = random.choice(USERS)
    new_ip = '203.0.113.50'  # Unusual IP
    resource = random.choice(CRITICAL_RESOURCES)
    
    print(f"\n🟡 Simulating anomalous access: {user} from new IP {new_ip}")
    
    event = {
        'type': 'access',
        'timestamp': time.time(),
        'user': user,
        'client_ip': new_ip,
        'resource_path': resource,
        'resource_type': 'database',
        'action': 'read',
        'status_code': 200,
        'bytes': 50000
    }
    await send_event(session, event)
    print(f"  🌐 Access from new location to critical resource")


async def run_demonstration():
    """Run complete security event demonstration"""
    print("=" * 70)
    print("🛡️  SIEM SECURITY EVENT DEMONSTRATION")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        # 1. Normal activity baseline
        print("\n📊 Phase 1: Generating normal activity baseline...")
        for _ in range(5):
            await generate_normal_activity(session)
            await asyncio.sleep(0.3)
        
        await asyncio.sleep(2)
        
        # 2. Brute force attack
        await simulate_brute_force_attack(session)
        await asyncio.sleep(2)
        
        # 3. Privilege escalation
        await simulate_privilege_escalation(session)
        await asyncio.sleep(2)
        
        # 4. Anomalous access
        await simulate_anomalous_access(session)
        await asyncio.sleep(2)
        
        # 5. More normal activity
        print("\n📊 Generating additional normal activity...")
        for _ in range(5):
            await generate_normal_activity(session)
            await asyncio.sleep(0.3)
    
    print("\n" + "=" * 70)
    print("✅ Demonstration complete!")
    print("🌐 Check dashboard at: http://localhost:8000/dashboard")
    print("=" * 70)


if __name__ == '__main__':
    asyncio.run(run_demonstration())
