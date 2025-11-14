"""Integration tests for structured logging system."""
import pytest
import asyncio
import json
from src.core.structured_logger import StructuredLogger
from src.validators.field_validators import ValidatorFactory
from src.context.context_providers import ContextManager


class TestIntegration:
    """Integration tests for complete system."""
    
    def setup_method(self):
        """Setup integrated system."""
        self.logger = StructuredLogger("integration-test-service")
        
        # Add validators
        validators = ValidatorFactory.create_web_api_validators()
        for validator in validators:
            self.logger.add_validator(validator)
            
        # Add context providers
        context_manager = ContextManager.create_web_app_context("integration-test", "1.0.0")
        for provider in context_manager.providers:
            self.logger.add_context_provider(provider)
            
    def test_complete_log_processing(self):
        """Test complete log processing pipeline."""
        entry = self.logger.info(
            "User performed action",
            user_id=12345,
            email="test@example.com",
            action="purchase",
            amount=99.99,
            trace_id="test-trace-123"
        )
        
        # Verify basic structure
        assert entry.message == "User performed action"
        assert entry.service_name == "integration-test-service"
        assert entry.trace_id == "test-trace-123"
        
        # Verify validated fields
        assert entry.fields["user_id"] == 12345
        assert entry.fields["email"] == "test@example.com"
        assert entry.fields["amount"] == 99.99
        
        # Verify context injection
        assert "hostname" in entry.context
        assert "app_name" in entry.context
        assert entry.context["app_name"] == "integration-test"
        
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        entry = self.logger.error(
            "Processing failed",
            user_id="invalid",  # Should be int
            email="bad-email",  # Invalid format
            amount=-50          # Invalid range
        )
        
        # Should contain validation errors but not break logging
        assert "user_id_validation_error" in entry.fields
        assert "email_validation_error" in entry.fields
        assert "amount_range_error" in entry.fields
        
    def test_high_volume_logging(self):
        """Test performance under high volume."""
        import time
        
        start_time = time.time()
        num_logs = 100
        
        for i in range(num_logs):
            self.logger.info(
                f"High volume test {i}",
                iteration=i,
                user_id=i + 1000,
                action="test"
            )
            
        end_time = time.time()
        duration = end_time - start_time
        logs_per_second = num_logs / duration
        
        # Should handle at least 50 logs per second
        assert logs_per_second > 50
        print(f"Performance: {logs_per_second:.1f} logs/second")
        
    def test_context_provider_failure_handling(self):
        """Test graceful handling of context provider failures."""
        class FailingContextProvider:
            def get_context(self):
                raise Exception("Context provider failed")
                
        self.logger.add_context_provider(FailingContextProvider())
        
        # Should still log successfully
        entry = self.logger.info("Test with failing context provider")
        
        # Should contain error information
        assert "context_error" in entry.context
        
    def test_serialization_performance(self):
        """Test JSON serialization performance."""
        from src.core.structured_logger import FastJSONSerializer
        
        serializer = FastJSONSerializer()
        
        # Create test log entry
        entry = self.logger.info(
            "Serialization test",
            user_id=12345,
            data={"complex": {"nested": "structure"}},
            items=[1, 2, 3, 4, 5]
        )
        
        import time
        start_time = time.time()
        
        # Serialize 1000 times
        for _ in range(1000):
            json_str = serializer.serialize(entry)
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast
        assert duration < 1.0  # Less than 1 second for 1000 serializations
        print(f"Serialization performance: {1000/duration:.1f} ops/second")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
