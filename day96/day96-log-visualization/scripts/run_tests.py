import subprocess
import sys
import os

def run_backend_tests():
    """Run backend tests"""
    print("🧪 Running backend tests...")
    os.chdir('backend')
    result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/', '-v'], 
                          capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    os.chdir('..')
    return result.returncode == 0

def run_frontend_tests():
    """Run frontend tests"""
    print("🧪 Running frontend tests...")
    os.chdir('frontend')
    result = subprocess.run(['npm', 'test', '--', '--watchAll=false'], 
                          capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    os.chdir('..')
    return result.returncode == 0

def main():
    print("🚀 Running all tests for Day 96: Data Visualization Components")
    print("=" * 60)
    
    backend_success = run_backend_tests()
    frontend_success = run_frontend_tests()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"Backend: {'✅ PASSED' if backend_success else '❌ FAILED'}")
    print(f"Frontend: {'✅ PASSED' if frontend_success else '❌ FAILED'}")
    
    if backend_success and frontend_success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
