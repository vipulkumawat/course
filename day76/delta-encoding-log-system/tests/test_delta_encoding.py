import pytest
import json
from datetime import datetime, timedelta
from src.compression.delta_encoder import DeltaEncoder, DeltaDecoder
from src.compression.models import LogEntry
from config.delta_config import DeltaEncodingConfig

class TestDeltaEncoding:
    def setup_method(self):
        self.config = DeltaEncodingConfig()
        self.encoder = DeltaEncoder(self.config)
        self.decoder = DeltaDecoder()
    
    def test_baseline_creation(self):
        """Test that first entry becomes baseline"""
        entry = LogEntry(
            timestamp="2025-05-16T10:00:00Z",
            level="INFO",
            service="test-service",
            message="Test message",
            metadata={"user_id": "123"}
        )
        
        result, compression_ratio = self.encoder.encode_entry(entry)
        assert result is None  # First entry should be baseline
        assert compression_ratio == 0.0
    
    def test_delta_compression(self):
        """Test delta compression between similar entries"""
        baseline = LogEntry(
            timestamp="2025-05-16T10:00:00Z",
            level="INFO",
            service="test-service",
            message="User login successful",
            metadata={"user_id": "123", "ip": "192.168.1.100"}
        )
        
        similar_entry = LogEntry(
            timestamp="2025-05-16T10:00:30Z",
            level="INFO",
            service="test-service",
            message="User login successful",
            metadata={"user_id": "124", "ip": "192.168.1.101"}
        )
        
        # Create baseline
        self.encoder.encode_entry(baseline)
        
        # Create delta
        delta, compression_ratio = self.encoder.encode_entry(similar_entry, baseline)
        
        assert delta is not None
        assert compression_ratio < 1.0  # Should achieve compression
        assert 'timestamp' in delta.field_deltas
        assert delta.field_deltas['timestamp']['type'] == 'time_delta'
    
    def test_reconstruction_accuracy(self):
        """Test that reconstructed entries match originals"""
        baseline = LogEntry(
            timestamp="2025-05-16T10:00:00Z",
            level="INFO",
            service="web-server",
            message="HTTP 200 - /api/users/123 - 45ms",
            metadata={"request_id": "req_001", "user_id": "123"}
        )
        
        modified_entry = LogEntry(
            timestamp="2025-05-16T10:00:15Z",
            level="INFO",
            service="web-server",
            message="HTTP 200 - /api/users/124 - 52ms",
            metadata={"request_id": "req_002", "user_id": "124"}
        )
        
        # Create delta
        delta, _ = self.encoder.encode_entry(modified_entry, baseline)
        
        # Reconstruct
        reconstructed = self.decoder.decode_entry(delta, baseline)
        
        # Verify accuracy
        assert reconstructed.timestamp == modified_entry.timestamp
        assert reconstructed.level == modified_entry.level
        assert reconstructed.service == modified_entry.service
        assert reconstructed.message == modified_entry.message
        assert reconstructed.metadata == modified_entry.metadata
    
    def test_compression_stats(self):
        """Test compression statistics tracking"""
        baseline = LogEntry(
            timestamp="2025-05-16T10:00:00Z",
            level="INFO",
            service="test",
            message="Test message",
            metadata={}
        )
        
        # Create multiple similar entries
        self.encoder.encode_entry(baseline)
        
        for i in range(5):
            entry = LogEntry(
                timestamp=f"2025-05-16T10:0{i:01d}:00Z",
                level="INFO",
                service="test",
                message="Test message",
                metadata={"sequence": i}
            )
            self.encoder.encode_entry(entry, baseline)
        
        stats = self.encoder.get_stats()
        assert stats['total_entries'] > 0
        assert stats['compressed_entries'] > 0
        assert stats['avg_compression_ratio'] > 0
    
    def test_string_delta_compression(self):
        """Test string delta compression for similar messages"""
        baseline = LogEntry(
            timestamp="2025-05-16T10:00:00Z",
            level="INFO",
            service="api",
            message="Processing request for user_id=12345",
            metadata={}
        )
        
        similar_entry = LogEntry(
            timestamp="2025-05-16T10:00:01Z",
            level="INFO",
            service="api",
            message="Processing request for user_id=12346",
            metadata={}
        )
        
        delta, compression_ratio = self.encoder.encode_entry(similar_entry, baseline)
        
        # Should achieve good compression due to similar messages
        assert compression_ratio < 0.8
        
        # Verify reconstruction
        reconstructed = self.decoder.decode_entry(delta, baseline)
        assert reconstructed.message == similar_entry.message

@pytest.mark.asyncio
async def test_api_endpoints():
    """Test API endpoints functionality"""
    from src.api.endpoints import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test sample log generation
    response = client.post("/api/generate-sample-logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert data["count"] > 0
    
    # Test log compression
    sample_logs = data["logs"][:10]  # Use first 10 logs
    compression_response = client.post(
        "/api/compress-logs",
        json={"logs": sample_logs}
    )
    assert compression_response.status_code == 200
    compression_data = compression_response.json()
    assert compression_data["success"] is True
    assert compression_data["compression_ratio"] < 1.0
    
    # Test stats endpoint
    stats_response = client.get("/api/stats")
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert "compression" in stats_data
    assert "storage" in stats_data
    assert "system" in stats_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
