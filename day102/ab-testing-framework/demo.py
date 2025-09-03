#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import time
import random

async def demo_ab_testing_framework():
    """Demonstrate A/B testing framework functionality"""
    print("🎬 A/B Testing Framework Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to be ready...")
    for i in range(30):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        print("✅ Backend is ready!")
                        break
        except:
            pass
        await asyncio.sleep(1)
    else:
        print("❌ Backend not ready after 30 seconds")
        return
    
    async with aiohttp.ClientSession() as session:
        # Demo 1: Feature flag evaluation
        print("\n🏁 Demo 1: Feature Flag Evaluation")
        print("-" * 30)
        
        users = [f"user_{i}" for i in range(1, 11)]
        flag_name = "new_dashboard_layout"
        
        for user_id in users:
            async with session.post(f"{base_url}/api/feature-flags/evaluate", 
                                  json={
                                      "flag_name": flag_name,
                                      "user_id": user_id,
                                      "user_attributes": {"tier": "premium"}
                                  }) as response:
                result = await response.json()
                status = "🟢 ENABLED" if result["is_enabled"] else "🔴 DISABLED"
                print(f"User {user_id}: {status} (variant: {result['variant']})")
        
        # Demo 2: Experiment assignment
        print("\n🧪 Demo 2: Experiment Assignment")
        print("-" * 30)
        
        experiment_id = 1
        assignments = {"control": 0, "treatment": 0}
        
        for user_id in users:
            async with session.post(f"{base_url}/api/feature-flags/assign",
                                  json={
                                      "user_id": user_id,
                                      "experiment_id": experiment_id
                                  }) as response:
                result = await response.json()
                variant = result["variant"]
                assignments[variant] += 1
                print(f"User {user_id}: Assigned to {variant.upper()}")
        
        print(f"\n📊 Assignment Distribution:")
        print(f"Control: {assignments['control']} users ({assignments['control']/len(users)*100:.1f}%)")
        print(f"Treatment: {assignments['treatment']} users ({assignments['treatment']/len(users)*100:.1f}%)")
        
        # Demo 3: Experiment results
        print("\n📈 Demo 3: Experiment Results")
        print("-" * 30)
        
        async with session.get(f"{base_url}/api/feature-flags/experiments/{experiment_id}/results") as response:
            results = await response.json()
            
            print(f"Experiment ID: {results['experiment_id']}")
            print(f"Total Users: {results['total_users']:,}")
            print(f"Control Users: {results['control_users']:,}")
            print(f"Treatment Users: {results['treatment_users']:,}")
            print(f"Control Conversion: {results['control_conversion']:.1%}")
            print(f"Treatment Conversion: {results['treatment_conversion']:.1%}")
            print(f"Statistical Significance: p = {results['statistical_significance']:.3f}")
            print(f"Confidence Interval: [{results['confidence_interval'][0]:.3f}, {results['confidence_interval'][1]:.3f}]")
            print(f"Recommendation: {results['recommendation']}")
        
        # Demo 4: Consistency test
        print("\n🔄 Demo 4: User Assignment Consistency")
        print("-" * 30)
        
        test_user = "consistency_test_user"
        
        # Test same user gets same assignment
        assignments = []
        for i in range(5):
            async with session.post(f"{base_url}/api/feature-flags/evaluate",
                                  json={
                                      "flag_name": flag_name,
                                      "user_id": test_user
                                  }) as response:
                result = await response.json()
                assignments.append(result["is_enabled"])
        
        consistent = all(a == assignments[0] for a in assignments)
        print(f"User {test_user}: {'✅ CONSISTENT' if consistent else '❌ INCONSISTENT'}")
        print(f"Assignments: {assignments}")
    
    print("\n🎉 Demo completed successfully!")
    print("🌐 Open http://localhost:3000 to see the dashboard")

if __name__ == "__main__":
    asyncio.run(demo_ab_testing_framework())
