"""Demo script for data sovereignty compliance"""
import requests
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def demo_classification():
    print_header("1. Log Classification Demo")
    
    test_logs = [
        {
            "id": "log-001",
            "message": "User john.doe@email.com logged in successfully",
            "level": "INFO",
            "service": "auth-service",
            "ip_address": "185.23.45.67",
            "user_location": "EU"
        },
        {
            "id": "log-002",
            "message": "Payment processed for order #12345",
            "level": "INFO",
            "service": "payment-service",
            "ip_address": "192.168.1.10",
            "user_location": "US"
        },
        {
            "id": "log-003",
            "message": "Patient medical record accessed",
            "level": "INFO",
            "service": "health-service",
            "ip_address": "203.45.67.89",
            "user_location": "APAC"
        }
    ]
    
    for log in test_logs:
        print(f"🔍 Classifying: {log['id']}")
        response = requests.post(f"{API_BASE}/classify", json=log)
        result = response.json()
        
        classification = result['classification']
        print(f"   📍 Location: {classification['data_subject_location']}")
        print(f"   🔒 Sensitivity: {classification['sensitivity']}")
        print(f"   📋 Regulations: {', '.join(classification['applicable_regulations'])}")
        print(f"   🚨 Contains PII: {classification['contains_pii']}")
        print()

def demo_storage_validation():
    print_header("2. Storage Validation Demo")
    
    test_cases = [
        {
            "log_entry": {
                "id": "log-004",
                "message": "EU user data processing",
                "user_location": "EU",
                "contains_pii": True
            },
            "target_region": "eu-west-1",
            "expected": "ALLOWED"
        },
        {
            "log_entry": {
                "id": "log-005",
                "message": "EU user data processing",
                "user_location": "EU",
                "contains_pii": True
            },
            "target_region": "us-east-1",
            "expected": "DENIED"
        }
    ]
    
    for case in test_cases:
        print(f"📦 Testing storage: {case['log_entry']['id']} -> {case['target_region']}")
        response = requests.post(f"{API_BASE}/validate/storage", json=case)
        result = response.json()
        
        decision = result['decision']
        status = "✅ ALLOWED" if decision['allowed'] else "❌ DENIED"
        print(f"   {status}: {decision['reason']}")
        print()

def demo_transfer_validation():
    print_header("3. Cross-Border Transfer Validation Demo")
    
    test_cases = [
        {
            "log_entry": {
                "id": "log-006",
                "message": "Transferring EU logs",
                "user_location": "EU",
                "email": "user@example.com"
            },
            "source_region": "eu-west-1",
            "target_region": "us-east-1"
        },
        {
            "log_entry": {
                "id": "log-007",
                "message": "US internal transfer",
                "user_location": "US"
            },
            "source_region": "us-east-1",
            "target_region": "us-west-2"
        }
    ]
    
    for case in test_cases:
        print(f"🌍 Testing transfer: {case['source_region']} -> {case['target_region']}")
        response = requests.post(f"{API_BASE}/validate/transfer", json=case)
        result = response.json()
        
        decision = result['decision']
        action = decision['action'].upper()
        print(f"   📋 Action: {action}")
        print(f"   📝 Reason: {decision['reason']}")
        print()

def demo_compliance_report():
    print_header("4. Compliance Report Demo")
    
    response = requests.get(f"{API_BASE}/compliance/report?hours=24")
    report = response.json()
    
    print(f"📊 Compliance Report (Last 24 hours)")
    print(f"   Total Events: {report['total_events']}")
    print(f"   Total Violations: {report['total_violations']}")
    print(f"   Compliance Rate: {report['compliance_rate']:.2f}%")
    print(f"\n   Storage by Region:")
    for region, count in report['storage_by_region'].items():
        print(f"      {region}: {count} logs")
    
    if report['violations_by_region']:
        print(f"\n   ⚠️  Violations by Region:")
        for region, count in report['violations_by_region'].items():
            print(f"      {region}: {count} violations")

if __name__ == "__main__":
    print("\n🚀 Data Sovereignty Compliance System Demo")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Wait for API to be ready
    print("\n⏳ Waiting for API to start...")
    time.sleep(2)
    
    try:
        demo_classification()
        demo_storage_validation()
        demo_transfer_validation()
        demo_compliance_report()
        
        print_header("✅ Demo Completed Successfully!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Please ensure the API is running: python src/api/main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
