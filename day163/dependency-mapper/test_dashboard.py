#!/usr/bin/env python3
"""
Test script to verify dashboard metrics are updating
"""
import asyncio
import websockets
import json
import sys

async def test_dashboard():
    try:
        uri = "ws://localhost:8765"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for initial data...")
            
            # Wait for init message
            init_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(init_msg)
            
            if data.get('type') == 'init':
                graph_data = data.get('data', {})
                nodes = graph_data.get('nodes', [])
                edges = graph_data.get('edges', [])
                
                print(f"\n✓ Dashboard Metrics:")
                print(f"  Services: {len(nodes)}")
                print(f"  Dependencies: {len(edges)}")
                
                if len(nodes) > 0 and len(edges) > 0:
                    print(f"\n✓ SUCCESS: Metrics are non-zero!")
                    print(f"  Sample services: {[n.get('label') for n in nodes[:5]]}")
                    return True
                else:
                    print(f"\n✗ FAILED: Metrics are zero!")
                    return False
            
            # Wait for updates
            print("\nWaiting for updates...")
            for i in range(5):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    update = json.loads(msg)
                    if update.get('type') == 'update':
                        dep = update.get('dependency', {})
                        print(f"  Update: {dep.get('caller')} -> {dep.get('callee')} ({dep.get('latency')}ms)")
                except asyncio.TimeoutError:
                    break
            
            return True
            
    except ConnectionRefusedError:
        print("✗ ERROR: Cannot connect to WebSocket server on port 8765")
        print("  Make sure the server is running: bash run_services.sh")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == '__main__':
    success = asyncio.run(test_dashboard())
    sys.exit(0 if success else 1)
