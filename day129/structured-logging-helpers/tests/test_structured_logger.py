"""Tests for structured logging helpers."""
import pytest
import json
from datetime import datetime
from src.core.structured_logger import StructuredLogger, LogLevel
from src.validators.field_validators import TypeValidator, EmailValidator, RequiredFieldsValidator
from src.context.context_providers import EnvironmentContextProvider, ApplicationContextProvider


class TestStructuredLogger:
    """Test structured logger functionality."""
    
    def setup_method(self):
        """Setup test logger."""
        self.logger = StructuredLogger("test-service")
        
    def test_basic_logging(self):
        """Test basic log creation."""
        entry = self.logger.info("Test message", user_id=123, action="login")
        
        assert entry.message == "Test message"
        assert entry.level == LogLevel.INFO
        assert entry.service_name == "test-service"
        assert entry.fields["user_id"] == 123
        assert entry.fields["action"] == "login"
        assert entry.trace_id is not None
        
    def test_log_levels(self):
        """Test all log levels."""
        debug_entry = self.logger.debug("Debug message")
        info_entry = self.logger.info("Info message")
        warning_entry = self.logger.warning("Warning message")
        error_entry = self.logger.error("Error message")
        critical_entry = self.logger.critical("Critical message")
        
        assert debug_entry.level == LogLevel.DEBUG
        assert info_entry.level == LogLevel.INFO
        assert warning_entry.level == LogLevel.WARNING
        assert error_entry.level == LogLevel.ERROR
        assert critical_entry.level == LogLevel.CRITICAL
        
    def test_context_injection(self):
        """Test automatic context injection."""
        # Add context provider
        env_provider = EnvironmentContextProvider()
        self.logger.add_context_provider(env_provider)
        
        entry = self.logger.info("Test with context")
        
        assert "hostname" in entry.context
        assert "pid" in entry.context
        assert "timestamp_ms" in entry.context
        
    def test_field_validation(self):
        """Test field validation."""
        # Add validators
        self.logger.add_validator(TypeValidator())
        self.logger.add_validator(EmailValidator())
        
        # Valid fields
        entry = self.logger.info("Valid test", user_id=123, email="test@example.com")
        assert entry.fields["user_id"] == 123
        assert entry.fields["email"] == "test@example.com"
        
        # Invalid fields
        entry = self.logger.info("Invalid test", user_id="not_a_number", email="invalid-email")
        assert "user_id_validation_error" in entry.fields
        assert "email_validation_error" in entry.fields


class TestFieldValidators:
    """Test field validation system."""
    
    def test_type_validator(self):
        """Test type validation and conversion."""
        validator = TypeValidator()
        
        # Valid conversion
        fields = {"user_id": "123", "amount": "45.67"}
        validated = validator.validate(fields)
        assert validated["user_id"] == 123
        assert validated["amount"] == 45.67
        
        # Invalid conversion
        fields = {"user_id": "not_a_number"}
        validated = validator.validate(fields)
        assert "user_id_validation_error" in validated
        
    def test_email_validator(self):
        """Test email format validation."""
        validator = EmailValidator()
        
        # Valid email
        fields = {"email": "test@example.com"}
        validated = validator.validate(fields)
        assert "email_validation_error" not in validated
        
        # Invalid email
        fields = {"email": "invalid-email"}
        validated = validator.validate(fields)
        assert "email_validation_error" in validated
        
    def test_required_fields_validator(self):
        """Test required fields validation."""
        validator = RequiredFieldsValidator(["user_id", "action"])
        
        # All required fields present
        fields = {"user_id": 123, "action": "login", "optional": "value"}
        validated = validator.validate(fields)
        assert "missing_required_fields" not in validated
        
        # Missing required fields
        fields = {"optional": "value"}
        validated = validator.validate(fields)
        assert "missing_required_fields" in validated
        assert validated["missing_required_fields"] == ["user_id", "action"]


class TestContextProviders:
    """Test context injection providers."""
    
    def test_environment_context_provider(self):
        """Test environment context."""
        provider = EnvironmentContextProvider()
        context = provider.get_context()
        
        assert "hostname" in context
        assert "pid" in context
        assert "python_version" in context
        assert "timestamp_ms" in context
        
    def test_application_context_provider(self):
        """Test application context."""
        provider = ApplicationContextProvider("test-app", "1.0.0", "production")
        context = provider.get_context()
        
        assert context["app_name"] == "test-app"
        assert context["version"] == "1.0.0"
        assert context["environment"] == "production"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
