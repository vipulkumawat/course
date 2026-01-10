"""Unit tests for Kubernetes Operator"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add src to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'src', 'operator'))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

class TestLogProcessorOperator:
    """Test LogProcessor operator functionality"""
    
    @patch('kubernetes.client.AppsV1Api')
    @patch('kubernetes.client.CoreV1Api')
    def test_create_deployment(self, mock_core, mock_apps):
        """Test deployment creation"""
        from main import LogProcessorOperator
        
        operator = LogProcessorOperator()
        spec = {
            'replicas': 3,
            'logLevel': 'ERROR',
            'resources': {
                'memory': '1Gi',
                'cpu': '500m'
            }
        }
        
        deployment = operator.create_deployment('test-processor', 'default', spec)
        
        assert deployment.metadata.name == 'test-processor-deployment'
        assert deployment.spec.replicas == 3
        assert deployment.spec.template.spec.containers[0].env[0].value == 'ERROR'
    
    @patch('kubernetes.client.AppsV1Api')
    @patch('kubernetes.client.CoreV1Api')
    def test_create_service(self, mock_core, mock_apps):
        """Test service creation"""
        from main import LogProcessorOperator
        
        operator = LogProcessorOperator()
        service = operator.create_service('test-processor', 'default')
        
        assert service.metadata.name == 'test-processor-service'
        assert service.spec.ports[0].port == 8080
    
    def test_operator_metrics_initialization(self):
        """Test operator metrics are initialized"""
        from main import LogProcessorOperator
        
        with patch('kubernetes.config.load_kube_config'):
            operator = LogProcessorOperator()
            
            assert 'reconciliations' in operator.metrics
            assert 'scaling_events' in operator.metrics
            assert 'errors' in operator.metrics


@pytest.mark.asyncio
async def test_api_stats_endpoint():
    """Test API stats endpoint"""
    try:
        from fastapi.testclient import TestClient
        
        # Mock Kubernetes API
        with patch('kubernetes.client.CustomObjectsApi') as mock_api:
            with patch('kubernetes.config.load_kube_config'):
                # Mock the list_cluster_custom_object to return empty list
                mock_instance = mock_api.return_value
                mock_instance.list_cluster_custom_object.return_value = {'items': []}
                
                from src.api.server import app
                
                client = TestClient(app)
                response = client.get("/api/stats")
                
                assert response.status_code == 200
                data = response.json()
                assert 'total_processors' in data
                assert 'ready_replicas' in data
    except ImportError:
        pytest.skip("fastapi or testclient not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
