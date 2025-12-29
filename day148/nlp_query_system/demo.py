#!/usr/bin/env python3
import asyncio
import httpx
import json
from datetime import datetime

async def demo():
    base_url = "http://localhost:8000"
    
    print("🎬 NLP Query System Demonstration")
    print("=" * 60)
    
    # Wait for service to be ready
    print("\n⏳ Waiting for service to start...")
    for _ in range(30):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/api/health")
                if response.status_code == 200:
                    print("✅ Service is ready!")
                    break
        except:
            await asyncio.sleep(1)
    
    # Test queries
    test_queries = [
        "Show me errors from payment service in the last hour",
        "How many warnings occurred today?",
        "Find logs from auth service",
        "What caused the errors?",
        "Count all errors"
    ]
    
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            print("-" * 60)
            
            try:
                response = await client.post(
                    f"{base_url}/api/query",
                    json={"query": query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {data['message']}")
                    print(f"Intent: {data['metadata']['intent']}")
                    print(f"Results: {len(data['results'])} logs")
                    if data.get('sql_query'):
                        print(f"SQL: {data['sql_query'][:100]}...")
                else:
                    print(f"❌ Error: {response.status_code}")
            
            except Exception as e:
                print(f"❌ Request failed: {e}")
            
            await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎉 Demo Complete!")
    print(f"🌐 Open http://localhost:8000 in your browser to try the UI")

if __name__ == "__main__":
    asyncio.run(demo())
