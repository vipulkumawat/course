import pytest
import asyncio
from src.pipeline.log_processor import LogProcessor

class TestLogProcessor:
    """Test suite for log processor functionality."""
    
    def setup_method(self):
        self.processor = LogProcessor()
    
    @pytest.mark.asyncio
    async def test_process_log_with_encryption(self):
        """Test log processing with field encryption."""
        log_entry = {
            "id": "log_001",
            "user_email": "john.doe@example.com",
            "phone": "555-123-4567",
            "request_id": "req_123",
            "timestamp": "2025-05-16T10:30:00Z"
        }
        
        processed = await self.processor.process_log(log_entry)
        
        # Check processing metadata
        assert '_processing' in processed
        assert 'encrypted_fields' in processed['_processing']
        
        # Check encrypted fields
        encrypted_fields = processed['_processing']['encrypted_fields']
        assert len(encrypted_fields) == 2  # email and phone
        
        field_names = [f['field_name'] for f in encrypted_fields]
        assert 'user_email' in field_names
        assert 'phone' in field_names
        
        # Check that sensitive fields are encrypted
        assert processed['user_email']['_encrypted'] == True
        assert processed['phone']['_encrypted'] == True
        
        # Check that non-sensitive fields remain unchanged
        assert processed['request_id'] == "req_123"
        assert processed['timestamp'] == "2025-05-16T10:30:00Z"
    
    @pytest.mark.asyncio
    async def test_process_log_no_sensitive_data(self):
        """Test log processing with no sensitive fields."""
        log_entry = {
            "id": "log_002",
            "request_id": "req_456",
            "timestamp": "2025-05-16T10:30:00Z",
            "status_code": 200,
            "response_time": 150
        }
        
        processed = await self.processor.process_log(log_entry)
        
        # Check processing metadata
        assert '_processing' in processed
        encrypted_fields = processed['_processing']['encrypted_fields']
        assert len(encrypted_fields) == 0
        
        # All fields should remain unchanged
        for key, value in log_entry.items():
            assert processed[key] == value
    
    @pytest.mark.asyncio
    async def test_decrypt_log(self):
        """Test log decryption functionality."""
        log_entry = {
            "id": "log_003",
            "user_email": "test@example.com",
            "request_id": "req_789"
        }
        
        # Encrypt first
        encrypted = await self.processor.process_log(log_entry)
        
        # Then decrypt
        decrypted = self.processor.decrypt_log(encrypted)
        
        # Should get back original values
        assert decrypted['user_email'] == "test@example.com"
        assert decrypted['request_id'] == "req_789"
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing of multiple logs."""
        log_entries = [
            {"id": "log_1", "user_email": "user1@example.com"},
            {"id": "log_2", "phone": "555-111-2222"},
            {"id": "log_3", "request_id": "req_999"}
        ]
        
        results = await self.processor.process_batch(log_entries)
        
        assert len(results) == 3
        
        # Check that exceptions weren't raised
        for result in results:
            assert not isinstance(result, Exception)
    
    def test_stats_tracking(self):
        """Test statistics tracking."""
        initial_stats = self.processor.get_stats()
        
        assert 'logs_processed' in initial_stats
        assert 'fields_encrypted' in initial_stats
        assert 'fields_detected' in initial_stats
        assert 'errors' in initial_stats
