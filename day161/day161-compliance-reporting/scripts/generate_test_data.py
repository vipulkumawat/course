import requests
import time
import random
from datetime import datetime

API_BASE = "http://localhost:8000"

# Sample test events
test_events = [
    {
        "event_type": "auth_failure",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "user": "john.doe@company.com",
            "action": "account_locked",
            "reason": "5 failed login attempts",
            "source_ip": "192.168.1.100"
        }
    },
    {
        "event_type": "data_access",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "user": "admin@company.com",
            "resource_type": "cardholder_data",
            "action": "read",
            "database": "payments_db"
        }
    },
    {
        "event_type": "admin_action",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "user": "root",
            "privilege_level": "admin",
            "action": "configuration_change",
            "target": "firewall_rules"
        }
    },
    {
        "event_type": "access_control",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "user": "developer@company.com",
            "result": "enforced",
            "resource": "production_database",
            "permission": "denied"
        }
    },
    {
        "event_type": "security_alert",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "severity": "high",
            "alert_type": "suspicious_activity",
            "description": "Multiple failed access attempts"
        }
    },
    {
        "event_type": "authentication",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "user": "jane.smith@company.com",
            "mfa_enabled": True,
            "mfa_method": "authenticator_app",
            "result": "success"
        }
    },
    {
        "event_type": "security_event",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "logged": True,
            "event_category": "network_intrusion_attempt",
            "source": "IDS"
        }
    },
    {
        "event_type": "phi_access",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "user": "doctor@hospital.com",
            "authorized": True,
            "patient_id": "P12345",
            "access_reason": "treatment"
        }
    },
    {
        "event_type": "audit_log",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "phi_involved": True,
            "action": "patient_record_view",
            "user": "nurse@hospital.com"
        }
    }
]

def generate_events(count=50):
    print(f"🔄 Generating {count} test security events...")
    
    for i in range(count):
        event = random.choice(test_events).copy()
        event["timestamp"] = datetime.now().isoformat()
        
        try:
            response = requests.post(f"{API_BASE}/api/events/ingest", json=event)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Event {i+1}: {result['compliance_matches']} matches, Evidence: {result['evidence_id']}")
            else:
                print(f"❌ Event {i+1}: Failed - {response.status_code}")
        except Exception as e:
            print(f"❌ Event {i+1}: Error - {str(e)}")
        
        time.sleep(0.1)
    
    print(f"✅ Generated {count} security events")

if __name__ == "__main__":
    generate_events(50)
