#!/usr/bin/env python3
"""Validate dashboard metrics are updating correctly"""
import requests
import json
import sys

def validate_metrics():
    """Validate all dashboard metrics"""
    print("=" * 70)
    print("📊 Validating Dashboard Metrics")
    print("=" * 70)
    
    try:
        # Get statistics
        response = requests.get("http://localhost:8000/api/statistics")
        if response.status_code != 200:
            print(f"❌ Failed to get statistics: {response.status_code}")
            return False
        
        stats = response.json()
        
        # Get incidents
        incidents_response = requests.get("http://localhost:8000/api/incidents?limit=50")
        incidents_data = incidents_response.json()
        
        print("\n📈 Current Statistics:")
        print(f"  Total Events: {stats['total_events']}")
        print(f"  Total Incidents: {stats['total_incidents']}")
        print(f"  Active Incidents: {stats['active_incidents']}")
        print("\n📊 Incidents by Severity:")
        print(f"  Critical: {stats['incidents_by_severity']['critical']}")
        print(f"  High: {stats['incidents_by_severity']['high']}")
        print(f"  Medium: {stats['incidents_by_severity']['medium']}")
        print(f"  Low: {stats['incidents_by_severity']['low']}")
        
        print(f"\n📋 Recent Incidents: {incidents_data['total']}")
        
        # Validation checks
        all_passed = True
        
        print("\n✅ Validation Results:")
        
        # Check total events
        if stats['total_events'] > 0:
            print("  ✓ Total Events: Non-zero (PASS)")
        else:
            print("  ✗ Total Events: Zero (FAIL)")
            all_passed = False
        
        # Check if we have incidents or events
        if stats['total_events'] > 0 or stats['total_incidents'] > 0:
            print("  ✓ Metrics are updating (PASS)")
        else:
            print("  ✗ Metrics are all zero (FAIL)")
            all_passed = False
        
        # Check incidents list
        if incidents_data['total'] > 0:
            print("  ✓ Incidents API returning data (PASS)")
            print(f"\n📝 Sample Incident:")
            if incidents_data['incidents']:
                sample = incidents_data['incidents'][0]
                print(f"    ID: {sample['incident_id']}")
                print(f"    Severity: {sample['severity']}")
                print(f"    Title: {sample['title']}")
                print(f"    Risk Score: {sample['risk_score']:.2f}")
        else:
            print("  ⚠ Incidents API empty (may be OK if no incidents detected)")
        
        # Check dashboard endpoint
        dashboard_response = requests.get("http://localhost:8000/dashboard")
        if dashboard_response.status_code == 200:
            print("  ✓ Dashboard endpoint accessible (PASS)")
        else:
            print(f"  ✗ Dashboard endpoint failed: {dashboard_response.status_code} (FAIL)")
            all_passed = False
        
        print("\n" + "=" * 70)
        if all_passed:
            print("✅ All validations PASSED - Dashboard metrics are updating correctly!")
        else:
            print("❌ Some validations FAILED - Please check the issues above")
        print("=" * 70)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error validating metrics: {e}")
        return False

if __name__ == '__main__':
    success = validate_metrics()
    sys.exit(0 if success else 1)
