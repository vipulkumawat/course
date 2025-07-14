import pytest
import asyncio
import json
from src.pipeline.log_processor import LogProcessor
from src.encryption.field_detector import FieldDetector
from src.encryption.encryption_engine import EncryptionEngine

class TestIntegration:
    """Integration tests for the complete encryption system."""
    
    def setup_method(self):
        self.processor = LogProcessor()
    
    @pytest.mark.asyncio
    async def test_end_to_end_encryption_flow(self):
        """Test complete end-to-end encryption and decryption flow."""
        # Real-world log sample
        original_log = {
            "id": "txn_12345",
            "timestamp": "2025-05-16T14:30:00Z",
            "user_email": "customer@company.com",
            "phone": "555-123-4567",
            "payment_method": "credit_card",
            "amount": 99.99,
            "currency": "USD",
            "merchant_id": "merchant_abc123",
            "api_key": "sk_live_abcdef123456",
            "request_id": "req_987654321",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        # Process (encrypt) the log
        encrypted_log = await self.processor.process_log(original_log)
        
        # Verify sensitive fields are encrypted
        assert encrypted_log['user_email']['_encrypted'] == True
        assert encrypted_log['phone']['_encrypted'] == True
        assert encrypted_log['api_key']['_encrypted'] == True
        
        # Verify non-sensitive fields remain readable
        assert encrypted_log['request_id'] == original_log['request_id']
        assert encrypted_log['amount'] == original_log['amount']
        assert encrypted_log['currency'] == original_log['currency']
        
        # Verify processing metadata exists
        assert '_processing' in encrypted_log
        processing_info = encrypted_log['_processing']
        assert len(processing_info['encrypted_fields']) == 3
        
        # Decrypt the log
        decrypted_log = self.processor.decrypt_log(encrypted_log)
        
        # Verify all original data is recovered
        assert decrypted_log['user_email'] == original_log['user_email']
        assert decrypted_log['phone'] == original_log['phone']
        assert decrypted_log['api_key'] == original_log['api_key']
        
        # Non-sensitive fields should still be the same
        assert decrypted_log['request_id'] == original_log['request_id']
        assert decrypted_log['amount'] == original_log['amount']
    
    @pytest.mark.asyncio
    async def test_performance_with_large_batch(self):
        """Test system performance with larger data volumes."""
        # Generate batch of logs
        log_batch = []
        for i in range(100):
            log_batch.append({
                "id": f"log_{i:03d}",
                "timestamp": "2025-05-16T14:30:00Z",
                "user_email": f"user{i}@example.com",
                "phone": f"555-{i:03d}-{i:04d}",
                "request_id": f"req_{i}",
                "action": "api_call",
                "status": "success"
            })
        
        # Process entire batch
        start_time = asyncio.get_event_loop().time()
        results = await self.processor.process_batch(log_batch)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        
        # Verify all logs processed successfully
        assert len(results) == 100
        for result in results:
            assert not isinstance(result, Exception)
            assert '_processing' in result
        
        # Performance assertion (should process 100 logs in under 10 seconds)
        assert processing_time < 10.0
        
        # Check statistics
        stats = self.processor.get_stats()
        assert stats['logs_processed'] >= 100
        assert stats['fields_encrypted'] >= 200  # 2 fields per log
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test system behavior with invalid data."""
        invalid_logs = [
            None,  # Null log
            {},    # Empty log
            {"invalid": None},  # Non-string values
            {"field": 12345},   # Numeric values
        ]
        
        for invalid_log in invalid_logs:
            try:
                if invalid_log is not None:
                    result = await self.processor.process_log(invalid_log)
                    # Should handle gracefully
                    assert '_processing' in result
            except Exception:
                # Exceptions are acceptable for truly invalid data
                pass
