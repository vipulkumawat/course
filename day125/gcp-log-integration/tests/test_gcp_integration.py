"""GCP Integration Tests"""
import pytest
from unittest.mock import Mock, patch
from src.gcp_client import GCPLoggingClient


class TestGCPLoggingClient:
    
    def test_client_initialization(self):
        """Test client can be instantiated"""
        client = GCPLoggingClient("test-project", "fake-credentials.json")
        assert client.project_id == "test-project"
        assert not client._authenticated
    
    @patch('src.gcp_client.service_account.Credentials.from_service_account_file')
    @patch('src.gcp_client.logging_v2')
    def test_authentication_success(self, mock_logging_v2, mock_creds):
        """Test successful authentication"""
        # Mock credentials
        mock_creds.return_value = Mock()
        
        # Mock LoggingServiceV2Client
        mock_client_instance = Mock()
        mock_logging_v2.LoggingServiceV2Client = Mock(return_value=mock_client_instance)
        
        client = GCPLoggingClient("test-project", "fake-credentials.json")
        result = client.authenticate()
        assert result is True
        assert client._authenticated is True
        assert client.client is not None
    
    def test_normalize_log_entry(self):
        """Test log entry normalization"""
        client = GCPLoggingClient("test-project", "fake-credentials.json")
        
        # Create mock log entry
        mock_entry = Mock()
        mock_entry.timestamp.isoformat.return_value = "2025-05-16T10:00:00Z"
        mock_entry.severity.name = "ERROR"
        mock_entry.text_payload = "Test error message"
        mock_entry.resource.type = "gce_instance"
        mock_entry.resource.labels = {"instance_id": "123"}
        mock_entry.labels = {}
        mock_entry.log_name = "projects/test/logs/syslog"
        mock_entry.insert_id = "abc123"
        
        normalized = client._normalize_log_entry(mock_entry)
        
        assert normalized['severity'] == "ERROR"
        assert normalized['cloud_provider'] == "gcp"
        assert normalized['project_id'] == "test-project"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
