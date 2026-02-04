#!/usr/bin/env python3
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

async def test_start():
    try:
        from src.main import SLASystem
        system = SLASystem()
        await system.init()
        print("✅ Initialization successful")
        await system.start()
        print("✅ Start successful")
        await asyncio.sleep(2)
        await system.stop()
        print("✅ Stop successful")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_start())
