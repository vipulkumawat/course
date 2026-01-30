#!/usr/bin/env python3
"""Verification script for Day 161 Compliance Reporting System"""
import requests
import json
import sys

API_BASE = "http://localhost:8000"

def verify_dashboard():
    """Verify dashboard metrics are populated"""
    try:
        response = requests.get(f"{API_BASE}/api/dashboard/stats")
        if response.status_code != 200:
            print(f"❌ API returned status {response.status_code}")
            return False
        
        data = response.json()
        
        print("📊 Dashboard Metrics Verification:")
        print(f"   Total Evidence: {data['total_evidence']}")
        
        all_non_zero = True
        all_100_percent = True
        
        for framework, stats in data['frameworks'].items():
            coverage = stats['coverage_percentage']
            reqs = stats['requirements_with_evidence']
            total = stats['total_requirements']
            
            print(f"   {framework.upper()}:")
            print(f"      Coverage: {coverage:.1f}%")
            print(f"      Requirements: {reqs}/{total}")
            print(f"      Status: {stats['status']}")
            
            if reqs == 0:
                all_non_zero = False
            if coverage != 100.0:
                all_100_percent = False
        
        if data['total_evidence'] == 0:
            print("❌ Total evidence is zero!")
            return False
        
        if not all_non_zero:
            print("⚠️  Some frameworks have zero requirements with evidence")
        
        print("\n✅ Dashboard metrics are populated and non-zero!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying dashboard: {e}")
        return False

if __name__ == "__main__":
    success = verify_dashboard()
    sys.exit(0 if success else 1)
