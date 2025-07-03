import sys
import os
import pytest
import requests
import time
import json
from typing import Dict, List

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from coordinator.hash_ring import ConsistentHashRing

class TestDistributedSearch:
    """Test suite for distributed search system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.nodes = ['node-1', 'node-2', 'node-3', 'node-4']
        self.ports = [8101, 8102, 8103, 8104]
        self.base_url = "http://localhost"
        
    def test_hash_ring_distribution(self):
        """Test that hash ring distributes terms across multiple nodes"""
        ring = ConsistentHashRing(self.nodes)
        
        # Test term distribution
        terms = ['error', 'login', 'database', 'payment', 'security', 'user', 'system']
        distribution = {}
        
        for term in terms:
            node = ring.get_node(term)
            distribution[node] = distribution.get(node, 0) + 1
        
        # Should distribute across multiple nodes
        assert len(distribution) > 1, f"Terms not distributed across nodes: {distribution}"
        print(f"✅ Hash ring distribution: {distribution}")
        
    def test_hash_ring_consistency(self):
        """Test that hash ring provides consistent node assignment"""
        ring = ConsistentHashRing(self.nodes)
        
        # Same term should always map to same node
        term = "test_term"
        node1 = ring.get_node(term)
        node2 = ring.get_node(term)
        node3 = ring.get_node(term)
        
        assert node1 == node2 == node3, f"Inconsistent node assignment: {node1}, {node2}, {node3}"
        print(f"✅ Hash ring consistency: '{term}' -> {node1}")
        
    def test_node_health(self):
        """Test that all nodes are healthy"""
        for i, port in enumerate(self.ports, 1):
            try:
                response = requests.get(f"{self.base_url}:{port}/health", timeout=5)
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                assert data["node_id"] == f"node-{i}"
                print(f"✅ Node-{i} healthy on port {port}")
            except requests.RequestException as e:
                pytest.fail(f"Node-{i} on port {port} not responding: {e}")
                
    def test_node_stats(self):
        """Test that nodes return valid statistics"""
        for i, port in enumerate(self.ports, 1):
            try:
                response = requests.get(f"{self.base_url}:{port}/stats", timeout=5)
                assert response.status_code == 200
                data = response.json()
                assert "node_id" in data
                assert "term_count" in data
                assert "document_count" in data
                assert "status" in data
                assert data["status"] == "active"
                print(f"✅ Node-{i} stats: {data['document_count']} docs, {data['term_count']} terms")
            except requests.RequestException as e:
                pytest.fail(f"Node-{i} stats endpoint failed: {e}")
                
    def test_document_indexing(self):
        """Test document indexing across nodes"""
        test_docs = [
            ("test_doc_1", "This is a test document with error messages"),
            ("test_doc_2", "Database connection test with login functionality"),
            ("test_doc_3", "Payment processing test with security features"),
            ("test_doc_4", "System monitoring test with user authentication")
        ]
        
        for doc_id, content in test_docs:
            # Index on a random node (simulating hash ring distribution)
            port = self.ports[hash(doc_id) % len(self.ports)]
            try:
                response = requests.post(
                    f"{self.base_url}:{port}/index",
                    params={"doc_id": doc_id, "content": content},
                    timeout=5
                )
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "indexed"
                assert data["doc_id"] == doc_id
                print(f"✅ Indexed {doc_id} on port {port}")
            except requests.RequestException as e:
                pytest.fail(f"Failed to index {doc_id}: {e}")
                
    def test_search_functionality(self):
        """Test search functionality across nodes"""
        search_terms = ["error", "database", "payment", "user"]
        
        for term in search_terms:
            total_results = 0
            for port in self.ports:
                try:
                    response = requests.post(
                        f"{self.base_url}:{port}/search",
                        json={"terms": [term]},
                        timeout=5
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert "documents" in data
                    assert "node_id" in data
                    
                    results_count = len(data["documents"])
                    total_results += results_count
                    
                    if results_count > 0:
                        print(f"  Port {port}: {results_count} results for '{term}'")
                        
                except requests.RequestException as e:
                    pytest.fail(f"Search failed on port {port}: {e}")
                    
            print(f"✅ Total results for '{term}': {total_results}")
            
    def test_multi_term_search(self):
        """Test search with multiple terms"""
        try:
            response = requests.post(
                f"{self.base_url}:8101/search",
                json={"terms": ["error", "login"]},
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            
            # Should find documents containing both terms
            print(f"✅ Multi-term search returned {len(data['documents'])} results")
            
        except requests.RequestException as e:
            pytest.fail(f"Multi-term search failed: {e}")
            
    def test_empty_search(self):
        """Test search with empty terms"""
        try:
            response = requests.post(
                f"{self.base_url}:8101/search",
                json={"terms": []},
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert len(data["documents"]) == 0
            print("✅ Empty search handled correctly")
            
        except requests.RequestException as e:
            pytest.fail(f"Empty search failed: {e}")
            
    def test_invalid_requests(self):
        """Test handling of invalid requests"""
        # Test invalid search request
        try:
            response = requests.post(
                f"{self.base_url}:8101/search",
                json={"invalid_field": "test"},
                timeout=5
            )
            # Should either return 400 or handle gracefully
            assert response.status_code in [200, 400, 422]
            print("✅ Invalid search request handled")
            
        except requests.RequestException as e:
            pytest.fail(f"Invalid search request failed: {e}")
            
    def test_performance(self):
        """Test search performance"""
        start_time = time.time()
        
        # Perform multiple searches
        for _ in range(10):
            try:
                response = requests.post(
                    f"{self.base_url}:8101/search",
                    json={"terms": ["error"]},
                    timeout=5
                )
                assert response.status_code == 200
            except requests.RequestException as e:
                pytest.fail(f"Performance test failed: {e}")
                
        end_time = time.time()
        avg_time = (end_time - start_time) / 10 * 1000  # Convert to milliseconds
        
        assert avg_time < 100, f"Average search time {avg_time:.2f}ms exceeds 100ms threshold"
        print(f"✅ Performance test passed: {avg_time:.2f}ms average")

def test_integration():
    """Integration test for the entire system"""
    print("🧪 Running integration test...")
    
    # Test that all components work together
    ring = ConsistentHashRing(['node-1', 'node-2', 'node-3', 'node-4'])
    
    # Test document distribution
    test_docs = [
        ("integration_doc_1", "Integration test document with error handling"),
        ("integration_doc_2", "Database integration test with user authentication"),
        ("integration_doc_3", "Payment integration test with security validation")
    ]
    
    for doc_id, content in test_docs:
        # Determine which node should handle this document
        node = ring.get_node(doc_id)
        node_num = int(node.split('-')[1])
        port = 8100 + node_num
        
        try:
            # Index the document
            response = requests.post(
                f"http://localhost:{port}/index",
                params={"doc_id": doc_id, "content": content},
                timeout=5
            )
            assert response.status_code == 200
            
            # Search for the document
            terms = content.lower().split()[:2]  # First two words
            response = requests.post(
                f"http://localhost:{port}/search",
                json={"terms": terms},
                timeout=5
            )
            assert response.status_code == 200
            data = response.json()
            
            # Should find our document
            found = any(doc["id"] == doc_id for doc in data["documents"])
            assert found, f"Document {doc_id} not found in search results"
            
            print(f"✅ Integration test passed for {doc_id}")
            
        except requests.RequestException as e:
            pytest.fail(f"Integration test failed for {doc_id}: {e}")

if __name__ == "__main__":
    # Run basic tests
    test_suite = TestDistributedSearch()
    test_suite.setup_method()
    
    print("🧪 Running distributed search tests...")
    
    test_suite.test_hash_ring_distribution()
    test_suite.test_hash_ring_consistency()
    test_suite.test_node_health()
    test_suite.test_node_stats()
    test_suite.test_document_indexing()
    test_suite.test_search_functionality()
    test_suite.test_multi_term_search()
    test_suite.test_empty_search()
    test_suite.test_invalid_requests()
    test_suite.test_performance()
    
    test_integration()
    
    print("🎉 All tests passed!") 