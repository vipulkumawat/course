import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from coordinator.hash_ring import ConsistentHashRing

def test_hash_ring():
    nodes = ['node-1', 'node-2', 'node-3', 'node-4']
    ring = ConsistentHashRing(nodes)
    
    # Test term distribution
    terms = ['error', 'login', 'database', 'payment', 'security']
    distribution = {}
    
    for term in terms:
        node = ring.get_node(term)
        distribution[node] = distribution.get(node, 0) + 1
    
    assert len(distribution) > 1
    print(f"✅ Hash ring test passed. Distribution: {distribution}")

if __name__ == "__main__":
    test_hash_ring()
