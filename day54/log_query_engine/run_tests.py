"""
Test runner for the query engine
"""
import sys
import os
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_tests():
    """Run all tests"""
    print("🧪 Running Query Engine Tests")
    print("=" * 40)
    
    # Run tests with pytest
    result = pytest.main([
        'tests/',
        '-v',
        '--tb=short',
        '--color=yes'
    ])
    
    if result == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {result}")
    
    return result

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
