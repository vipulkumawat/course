#!/usr/bin/env python3
"""Test runner for field-level encryption system."""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Run all tests."""
    print("🚀 Running Field-Level Encryption Test Suite")
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        ("python -m pytest tests/unit/test_field_detector.py -v", "Field Detector Unit Tests"),
        ("python -m pytest tests/unit/test_encryption_engine.py -v", "Encryption Engine Unit Tests"),
        ("python -m pytest tests/unit/test_log_processor.py -v", "Log Processor Unit Tests"),
        ("python -m pytest tests/integration/test_integration.py -v", "Integration Tests"),
        ("python demo.py", "Demo Execution"),
    ]
    
    passed = 0
    total = len(tests)
    
    for command, description in tests:
        if run_command(command, description):
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for production.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
