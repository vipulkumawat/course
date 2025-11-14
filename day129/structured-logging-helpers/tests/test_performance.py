"""Performance tests for structured logging system."""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from src.core.structured_logger import StructuredLogger
from src.validators.field_validators import ValidatorFactory


class TestPerformance:
    """Performance benchmarks for structured logging."""
    
    def setup_method(self):
        """Setup performance test environment."""
        self.logger = StructuredLogger("performance-test")
        
        # Add realistic validators
        validators = ValidatorFactory.create_web_api_validators()
        for validator in validators:
            self.logger.add_validator(validator)
            
    def test_single_thread_throughput(self):
        """Measure single-thread logging throughput."""
        num_logs = 1000
        start_time = time.time()
        
        for i in range(num_logs):
            self.logger.info(
                f"Performance test log {i}",
                user_id=i,
                action="test",
                timestamp=time.time()
            )
            
        end_time = time.time()
        duration = end_time - start_time
        throughput = num_logs / duration
        
        print(f"Single-thread throughput: {throughput:.1f} logs/second")
        assert throughput > 100  # Should handle at least 100 logs/second
        
    def test_multi_thread_throughput(self):
        """Measure multi-thread logging throughput."""
        num_threads = 4
        logs_per_thread = 250
        total_logs = num_threads * logs_per_thread
        
        def log_worker(thread_id):
            for i in range(logs_per_thread):
                self.logger.info(
                    f"Multi-thread test from thread {thread_id}",
                    thread_id=thread_id,
                    iteration=i,
                    user_id=thread_id * 1000 + i
                )
                
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(log_worker, i) for i in range(num_threads)]
            for future in futures:
                future.result()
                
        end_time = time.time()
        duration = end_time - start_time
        throughput = total_logs / duration
        
        print(f"Multi-thread throughput: {throughput:.1f} logs/second")
        assert throughput > 200  # Should handle at least 200 logs/second with 4 threads
        
    def test_memory_usage(self):
        """Test memory usage during high-volume logging."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate many logs
        for i in range(5000):
            self.logger.info(
                f"Memory test log {i}",
                user_id=i,
                data={"key": f"value_{i}"},
                large_field="x" * 100  # Some larger data
            )
            
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.1f} MB for 5000 logs")
        # Should not use excessive memory (less than 50MB increase)
        assert memory_increase < 50 * 1024 * 1024
        
    def test_validation_overhead(self):
        """Measure overhead of field validation."""
        # Test without validation
        logger_no_validation = StructuredLogger("no-validation")
        
        num_logs = 1000
        
        # Time without validation
        start_time = time.time()
        for i in range(num_logs):
            logger_no_validation.info("Test", user_id=i, email=f"user{i}@example.com")
        no_validation_time = time.time() - start_time
        
        # Time with validation
        start_time = time.time()
        for i in range(num_logs):
            self.logger.info("Test", user_id=i, email=f"user{i}@example.com")
        validation_time = time.time() - start_time
        
        overhead_percent = ((validation_time - no_validation_time) / no_validation_time) * 100
        
        print(f"Validation overhead: {overhead_percent:.1f}%")
        # Validation should add less than 100% overhead
        assert overhead_percent < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
