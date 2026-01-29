"""Demonstration of UBA system"""
import requests
import time
import json
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"

def generate_normal_behavior(user: str, count: int = 50):
    """Generate normal user behavior for baseline"""
    print(f"\n📊 Generating {count} normal events for {user}...")
    
    for i in range(count):
        # Normal business hours
        hour = random.choice(range(9, 18))
        dt = (datetime.now() - timedelta(days=random.randint(0, 14))).replace(hour=hour)
        
        event = {
            "user": user,
            "event_type": random.choice(['login', 'access', 'download']),
            "timestamp": dt.isoformat(),
            "details": {
                "resource": random.choice(['/api/users', '/api/reports', '/api/data']),
                "bytes": random.randint(1000, 100000)
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/analyze", json=event)
        if response.status_code == 200:
            result = response.json()
            if i % 10 == 0:
                print(f"  Event {i+1}/{count}: Risk={result.get('risk_score', 0)} ({result.get('risk_level', 'learning')})")
        
        time.sleep(0.1)
    
    print(f"✅ Baseline established for {user}")

def simulate_anomaly(user: str, anomaly_type: str):
    """Simulate anomalous behavior"""
    print(f"\n🚨 Simulating {anomaly_type} for {user}...")
    
    response = requests.post(
        f"{BASE_URL}/api/simulate-anomaly",
        json={"user": user, "anomaly_type": anomaly_type}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"  Risk Score: {result.get('risk_score', 0)}")
        print(f"  Risk Level: {result.get('risk_level', 'unknown')}")
        print(f"  Anomalies: {', '.join(result.get('anomalies', []))}")
    
    return response.json()

def main():
    print("=" * 60)
    print("🔍 User Behavior Analytics - System Demonstration")
    print("=" * 60)
    
    # Wait for service to be ready
    print("\n⏳ Waiting for UBA service...")
    for _ in range(30):
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code == 200:
                print("✅ Service is ready!")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("❌ Service not available")
        return
    
    # Generate normal behavior for users
    users = ['alice', 'bob', 'charlie']
    
    for user in users:
        generate_normal_behavior(user, count=120)  # Generate enough to train baseline
    
    # Get stats
    print("\n📈 Current System Stats:")
    response = requests.get(f"{BASE_URL}/api/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"  Total Users: {stats.get('total_users', 0)}")
        print(f"  Trained Users: {stats.get('trained_users', 0)}")
        print(f"  Total Alerts: {stats.get('total_alerts', 0)}")
    
    # Simulate anomalies - create high-risk scenarios
    print("\n" + "=" * 60)
    print("Testing Anomaly Detection")
    print("=" * 60)
    
    # Generate multiple high-risk events to trigger alerts
    time.sleep(2)
    for _ in range(5):
        # Create extreme access pattern
        event = {
            "user": "alice",
            "event_type": "access",
            "timestamp": datetime.now().replace(hour=3, minute=0).isoformat(),  # 3 AM
            "details": {
                "resource": "/sensitive/database",
                "count": 10000  # Very high access count
            }
        }
        requests.post(f"{BASE_URL}/api/analyze", json=event)
        time.sleep(0.5)
    
    time.sleep(2)
    # Create extreme download
    for _ in range(3):
        event = {
            "user": "bob",
            "event_type": "download",
            "timestamp": datetime.now().replace(hour=2, minute=0).isoformat(),  # 2 AM
            "details": {
                "bytes": 50000000000  # 50GB - extreme
            }
        }
        requests.post(f"{BASE_URL}/api/analyze", json=event)
        time.sleep(0.5)
    
    time.sleep(2)
    # Multiple failed logins
    for _ in range(10):
        event = {
            "user": "charlie",
            "event_type": "failed_login",
            "timestamp": datetime.now().isoformat()
        }
        requests.post(f"{BASE_URL}/api/analyze", json=event)
        time.sleep(0.2)
    
    # Get alerts
    print("\n📋 Recent Alerts:")
    response = requests.get(f"{BASE_URL}/api/alerts")
    if response.status_code == 200:
        data = response.json()
        alerts = data.get('alerts', [])
        
        if alerts:
            for alert in alerts[-5:]:
                print(f"\n  🚨 {alert['user']} - Risk: {alert['risk_score']} ({alert['risk_level']})")
                print(f"     Time: {alert['timestamp']}")
                print(f"     Anomalies: {', '.join(alert.get('anomalies', []))}")
        else:
            print("  No alerts found")
    
    print("\n" + "=" * 60)
    print("✅ Demonstration Complete!")
    print(f"🌐 Dashboard: {BASE_URL}/dashboard")
    print("=" * 60)

if __name__ == '__main__':
    main()
