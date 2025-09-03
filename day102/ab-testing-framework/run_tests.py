#!/usr/bin/env python3
import subprocess
import sys
import os

def run_tests():
    """Run all tests for the A/B testing framework"""
    print("🧪 Running A/B Testing Framework Tests")
    print("=" * 50)
    
    # Activate virtual environment
    venv_python = "venv/bin/python" if os.name != 'nt' else "venv\\Scripts\\python.exe"
    
    # Run backend tests
    print("\n🐍 Running Backend Tests...")
    os.chdir("backend")
    
    result = subprocess.run([
        "../" + venv_python, "-m", "pytest", 
        "tests/", "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    os.chdir("..")
    
    if result.returncode == 0:
        print("✅ Backend tests passed!")
    else:
        print("❌ Backend tests failed!")
        return False
    
    # Test API endpoints
    print("\n🌐 Testing API Endpoints...")
    result = subprocess.run([venv_python, "demo.py"], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("✅ API tests passed!")
        return True
    else:
        print("❌ API tests failed!")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
