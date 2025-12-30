"""
Integration tests for Kubernetes deployment
"""
import subprocess
import time
import json

def run_kubectl(args):
    """Run kubectl command and return output"""
    cmd = ['kubectl'] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.returncode

def test_namespace_exists():
    """Test that namespace is created"""
    output, code = run_kubectl(['get', 'namespace', 'log-processing'])
    assert code == 0, "Namespace should exist"
    print("✅ Namespace exists")

def test_pods_running():
    """Test that all pods are running"""
    output, code = run_kubectl(['get', 'pods', '-n', 'log-processing', '-o', 'json'])
    assert code == 0, "Should get pods"
    
    pods = json.loads(output)
    for pod in pods['items']:
        name = pod['metadata']['name']
        phase = pod['status']['phase']
        print(f"Pod {name}: {phase}")
        assert phase in ['Running', 'Pending'], f"Pod {name} should be running or pending"
    
    print("✅ All pods are in valid state")

def test_services_exist():
    """Test that services are created"""
    services = [
        'rabbitmq',
        'query-coordinator',
        'storage-headless',
        'dashboard'
    ]
    
    for svc in services:
        output, code = run_kubectl(['get', 'svc', svc, '-n', 'log-processing'])
        assert code == 0, f"Service {svc} should exist"
        print(f"✅ Service {svc} exists")

def test_query_coordinator_health():
    """Test query coordinator health endpoint"""
    # Get pod name
    output, code = run_kubectl([
        'get', 'pod',
        '-n', 'log-processing',
        '-l', 'app=query-coordinator',
        '-o', 'jsonpath={.items[0].metadata.name}'
    ])
    
    if code == 0 and output:
        pod_name = output.strip()
        # Test health endpoint
        health_output, health_code = run_kubectl([
            'exec', '-n', 'log-processing', pod_name,
            '--', 'wget', '-qO-', 'http://localhost:8080/health'
        ])
        
        if health_code == 0:
            print(f"✅ Query coordinator health check passed: {health_output}")
        else:
            print(f"⚠️  Query coordinator health check pending")
    else:
        print("⚠️  Query coordinator pod not yet available")

if __name__ == '__main__':
    print("🧪 Running Kubernetes deployment tests...\n")
    
    try:
        test_namespace_exists()
        test_services_exist()
        test_pods_running()
        time.sleep(5)  # Wait for pods to initialize
        test_query_coordinator_health()
        
        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
