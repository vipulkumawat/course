#!/usr/bin/env python3
"""Test script for the deployment dashboard"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(name, method="GET", url="", data=None):
    """Test an endpoint and return the result"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}", timeout=5)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        else:
            return False, f"Unknown method: {method}"
        
        success = response.status_code == 200
        return success, response
    except requests.exceptions.ConnectionError:
        return False, "Connection failed - is the server running?"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("🧪 Testing Multi-Cloud Deployment Dashboard")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Main dashboard page
    print("1. Testing main dashboard page (/)...")
    success, result = test_endpoint("Main Dashboard", "GET", "/")
    if success:
        if isinstance(result, requests.Response):
            if "Multi-Cloud Deployment Dashboard" in result.text:
                print("   ✅ Dashboard page loads correctly")
                tests_passed += 1
            else:
                print("   ❌ Dashboard content not found")
                tests_failed += 1
        else:
            print(f"   ❌ {result}")
            tests_failed += 1
    else:
        print(f"   ❌ {result}")
        tests_failed += 1
    print()
    
    # Test 2-4: API status endpoints
    environments = ["dev", "staging", "prod"]
    for env in environments:
        print(f"2.{environments.index(env)+1}. Testing API status for {env}...")
        success, result = test_endpoint(f"Status {env}", "GET", f"/api/status/{env}")
        if success and isinstance(result, requests.Response):
            try:
                data = result.json()
                if data.get("environment") == env and "resource_counts" in data:
                    print(f"   ✅ {env} status API working")
                    print(f"      - Total resources: {data.get('total_resources', 0)}")
                    print(f"      - Monthly cost: ${data.get('estimated_costs', {}).get('monthly', 0)}")
                    print(f"      - Status: {data.get('status', 'unknown')}")
                    tests_passed += 1
                else:
                    print(f"   ❌ Invalid response structure")
                    tests_failed += 1
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON response")
                tests_failed += 1
        else:
            print(f"   ❌ {result}")
            tests_failed += 1
        print()
    
    # Test 5: Deployment endpoint
    print("5. Testing deployment endpoint...")
    deploy_data = {"environment": "dev", "cloud": "aws"}
    success, result = test_endpoint("Deploy", "POST", "/api/deploy", deploy_data)
    if success and isinstance(result, requests.Response):
        try:
            data = result.json()
            if "message" in data and "status" in data:
                print("   ✅ Deployment endpoint working")
                print(f"      - Message: {data.get('message')}")
                print(f"      - Status: {data.get('status')}")
                tests_passed += 1
            else:
                print(f"   ❌ Invalid response structure")
                tests_failed += 1
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
            tests_failed += 1
    else:
        print(f"   ❌ {result}")
        tests_failed += 1
    print()
    
    # Test 6: Invalid environment
    print("6. Testing invalid environment handling...")
    success, result = test_endpoint("Invalid env", "GET", "/api/status/invalid")
    if success and isinstance(result, requests.Response):
        try:
            data = result.json()
            # Should still return valid JSON even for invalid env
            if "environment" in data:
                print("   ✅ Invalid environment handled gracefully")
                tests_passed += 1
            else:
                print(f"   ❌ Unexpected response")
                tests_failed += 1
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response")
            tests_failed += 1
    else:
        print(f"   ❌ {result}")
        tests_failed += 1
    print()
    
    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📈 Success Rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    print("=" * 60)
    
    if tests_failed == 0:
        print("🎉 All tests passed! Dashboard is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
