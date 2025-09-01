#!/usr/bin/env python3

import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": "Bearer demo-token",
    "Content-Type": "application/json"
}

def demo_preferences_api():
    """Demonstrate the preferences API"""
    print("🎬 Day 98: User Preferences System Demo")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing API health...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"   ✅ Health check: {response.json()}")
    except:
        print("   ❌ Backend not running. Please start with ./start.sh")
        return
    
    # Get initial preferences
    print("\n2. Getting initial preferences...")
    try:
        response = requests.get(f"{API_BASE}/preferences", headers=HEADERS)
        preferences = response.json()
        print(f"   📋 Current preferences: {json.dumps(preferences, indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Update a preference
    print("\n3. Updating dashboard preference...")
    try:
        update_data = {
            "category": "dashboard",
            "key": "auto_refresh",
            "value": True
        }
        response = requests.put(
            f"{API_BASE}/preferences", 
            headers=HEADERS,
            json=update_data
        )
        result = response.json()
        print(f"   ✅ Update result: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Bulk update preferences
    print("\n4. Bulk updating preferences...")
    try:
        bulk_data = {
            "preferences": {
                "theme": {
                    "theme": "dark"
                },
                "notifications": {
                    "email_alerts": True,
                    "sound_enabled": False
                }
            }
        }
        response = requests.put(
            f"{API_BASE}/preferences/bulk",
            headers=HEADERS,
            json=bulk_data
        )
        result = response.json()
        print(f"   ✅ Bulk update result: {result}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Get updated preferences
    print("\n5. Getting updated preferences...")
    try:
        response = requests.get(f"{API_BASE}/preferences", headers=HEADERS)
        preferences = response.json()
        print(f"   📋 Updated preferences: {json.dumps(preferences, indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ Demo completed!")
    print("🌐 Visit http://localhost:3000 to see the frontend")
    print("📊 Visit http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    demo_preferences_api()
