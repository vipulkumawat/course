"""Main application demonstrating structured logging helpers."""
import asyncio
import random
import time
from core.structured_logger import StructuredLogger, LogLevel
from validators.field_validators import ValidatorFactory
from context.context_providers import ContextManager, EnvironmentContextProvider, ApplicationContextProvider


class StructuredLoggingDemo:
    """Demonstration of structured logging helpers."""
    
    def __init__(self):
        # Create logger with service name
        self.logger = StructuredLogger("demo-service")
        
        # Setup validators
        validators = ValidatorFactory.create_web_api_validators()
        for validator in validators:
            self.logger.add_validator(validator)
            
        # Setup context providers
        context_manager = ContextManager.create_web_app_context("structured-logging-demo", "1.0.0")
        for provider in context_manager.providers:
            self.logger.add_context_provider(provider)
            
        print("🚀 Structured Logging Demo Initialized")
        print("=" * 50)
        
    def demonstrate_basic_logging(self):
        """Show basic structured logging."""
        print("\n📝 Basic Structured Logging:")
        print("-" * 30)
        
        self.logger.info("User authentication successful", 
                        user_id=12345, 
                        email="john.doe@example.com",
                        login_method="oauth")
                        
        self.logger.warning("High response time detected",
                           endpoint="/api/users",
                           response_time=2.5,
                           status_code=200)
                           
        self.logger.error("Payment processing failed",
                         user_id=67890,
                         amount=99.99,
                         error_code="INSUFFICIENT_FUNDS")
                         
    def demonstrate_validation(self):
        """Show field validation in action."""
        print("\n🔍 Field Validation Demo:")
        print("-" * 30)
        
        # Valid fields
        self.logger.info("Valid user registration",
                        user_id=12345,
                        email="valid@example.com",
                        amount=50.0)
                        
        # Invalid fields (will show validation errors)
        self.logger.info("Invalid field examples",
                        user_id="not_a_number",  # Should be int
                        email="invalid-email",   # Invalid format
                        amount=-100)             # Negative amount
                        
    def demonstrate_context_injection(self):
        """Show automatic context injection."""
        print("\n🎯 Context Injection Demo:")
        print("-" * 30)
        
        self.logger.info("Order processing started",
                        order_id="ORD-001",
                        customer_type="premium")
                        
        # Context is automatically injected (hostname, PID, etc.)
        
    def demonstrate_performance_logging(self):
        """Show performance-related logging."""
        print("\n⚡ Performance Logging Demo:")
        print("-" * 30)
        
        # Simulate API call timing
        start_time = time.time()
        time.sleep(0.1)  # Simulate work
        duration = time.time() - start_time
        
        self.logger.info("API call completed",
                        endpoint="/api/orders",
                        method="GET",
                        response_time=duration,
                        status_code=200,
                        response_size=1024)
                        
    def simulate_real_world_scenario(self):
        """Simulate a real-world application scenario."""
        print("\n🌍 Real-World Simulation:")
        print("-" * 30)
        
        scenarios = [
            {
                "action": "user_login",
                "level": "info",
                "fields": {"user_id": random.randint(1000, 9999), "success": True}
            },
            {
                "action": "payment_processed", 
                "level": "info",
                "fields": {"amount": round(random.uniform(10, 500), 2), "currency": "USD"}
            },
            {
                "action": "api_error",
                "level": "error", 
                "fields": {"status_code": 500, "error": "Database timeout"}
            },
            {
                "action": "cache_miss",
                "level": "warning",
                "fields": {"cache_key": f"user:{random.randint(1000, 9999)}", "ttl": 300}
            }
        ]
        
        for scenario in scenarios:
            if scenario["level"] == "info":
                self.logger.info(f"{scenario['action']} event", **scenario["fields"])
            elif scenario["level"] == "warning":
                self.logger.warning(f"{scenario['action']} event", **scenario["fields"])
            elif scenario["level"] == "error":
                self.logger.error(f"{scenario['action']} event", **scenario["fields"])
                
            time.sleep(0.5)  # Small delay between logs
            
    def run_comprehensive_demo(self):
        """Run all demonstrations."""
        print("🎬 Starting Comprehensive Structured Logging Demo")
        print("=" * 60)
        
        self.demonstrate_basic_logging()
        time.sleep(1)
        
        self.demonstrate_validation()
        time.sleep(1)
        
        self.demonstrate_context_injection()
        time.sleep(1)
        
        self.demonstrate_performance_logging()
        time.sleep(1)
        
        self.simulate_real_world_scenario()
        
        print("\n✅ Demo Complete!")
        print("=" * 60)


if __name__ == "__main__":
    demo = StructuredLoggingDemo()
    demo.run_comprehensive_demo()
