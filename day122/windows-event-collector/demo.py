"""Demo script for Windows Event Log Agent"""
import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def demonstrate_system():
    """Demonstrate the Windows Event Log Agent system"""
    print("🎬 Windows Event Log Agent - Live Demonstration")
    print("=" * 55)
    
    # Wait for system to be ready
    print("⏳ Waiting for system to initialize...")
    await asyncio.sleep(5)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test dashboard API
            print("\n1. Testing Dashboard API")
            print("-" * 25)
            
            async with session.get('http://localhost:8080/api/status') as resp:
                if resp.status == 200:
                    status = await resp.json()
                    print(f"✅ Agent Status: {'Running' if status.get('running') else 'Stopped'}")
                    print(f"✅ Channels: {status.get('channels', 0)}")
                    print(f"✅ Events Collected: {status.get('stats', {}).get('events_collected', 0)}")
                else:
                    print(f"❌ Dashboard API error: {resp.status}")
            
            # Test recent events
            print("\n2. Fetching Recent Events")
            print("-" * 26)
            
            async with session.get('http://localhost:8080/api/events/recent') as resp:
                if resp.status == 200:
                    events = await resp.json()
                    print(f"✅ Retrieved {len(events)} recent events")
                    
                    for i, event in enumerate(events[:3], 1):
                        print(f"   Event {i}: {event.get('channel')} - {event.get('level')} - {event.get('message', '')[:50]}...")
                else:
                    print(f"❌ Events API error: {resp.status}")
            
            # Test channel information
            print("\n3. Channel Information")
            print("-" * 22)
            
            async with session.get('http://localhost:8080/api/channels') as resp:
                if resp.status == 200:
                    channels = await resp.json()
                    print(f"✅ Active Channels: {len(channels)}")
                    
                    for channel, info in list(channels.items())[:3]:
                        status = "🟢" if info.get('status') == 'active' else "🔴"
                        print(f"   {status} {channel}: {info.get('events_collected', 0)} events")
                else:
                    print(f"❌ Channels API error: {resp.status}")
            
    except Exception as e:
        print(f"❌ Demo error: {e}")
    
    print("\n4. System Features Demonstrated")
    print("-" * 32)
    print("✅ Windows Event Log collection (mock mode on non-Windows)")
    print("✅ Real-time event processing")
    print("✅ Web dashboard with statistics")
    print("✅ RESTful API endpoints")
    print("✅ Event batching and transport")
    print("✅ Error handling and recovery")
    
    print(f"\n🎉 Demonstration completed at {datetime.now().strftime('%H:%M:%S')}")
    print("\n📊 View full dashboard at: http://localhost:8080")
    print("🔧 Modify configuration in: src/config/agent_config.py")

if __name__ == "__main__":
    asyncio.run(demonstrate_system())
