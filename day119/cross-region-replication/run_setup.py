#!/usr/bin/env python3
"""
Main setup and run script for Day 119: Cross-Region Data Replication
"""
import subprocess
import sys
import time
import os
import asyncio

def run_command(command, description, check=True):
    """Run a shell command with error handling"""
    print(f"📋 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stdout:
            print(f"   📤 Output: {e.stdout}")
        if e.stderr:
            print(f"   📥 Error: {e.stderr}")
        return False

def main():
    print("🌍 Day 119: Cross-Region Data Replication System Setup")
    print("=" * 60)
    
    # Build the system
    print("\n🏗️ Building system...")
    if not run_command("bash scripts/build.sh", "Building backend and frontend"):
        print("❌ Build failed!")
        return 1
    
    # Run tests
    print("\n🧪 Running tests...")
    if not run_command("bash scripts/test.sh", "Running comprehensive test suite"):
        print("⚠️ Some tests failed, but continuing...")
    
    # Start the system
    print("\n🚀 Starting system...")
    
    # Start in background
    server_process = subprocess.Popen(
        ["bash", "scripts/start.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("   ⏳ Waiting for server to start...")
    time.sleep(10)
    
    # Run demo
    print("\n🎭 Running system demonstration...")
    if not run_command("python scripts/demo.py", "Running demo script"):
        print("⚠️ Demo had issues, but system is running")
    
    print("\n" + "=" * 60)
    print("✅ Cross-Region Data Replication System is running!")
    print("🌐 Web Dashboard: http://localhost:8000")
    print("📡 WebSocket Updates: ws://localhost:8000/ws")
    print("🔗 API Docs: http://localhost:8000/docs")
    print("\n🛑 Press Ctrl+C to stop the system")
    
    try:
        # Keep running
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        server_process.terminate()
        run_command("bash scripts/stop.sh", "Cleaning up processes", check=False)
        print("✅ System stopped successfully!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
