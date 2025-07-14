import pytest
from src.encryption.field_detector import FieldDetector, DetectedField

class TestFieldDetector:
    """Test suite for field detection functionality."""
    
    def setup_method(self):
        self.detector = FieldDetector()
    
    def test_email_detection(self):
        """Test email pattern detection."""
        log_entry = {
            "user_email": "john.doe@example.com",
            "request_id": "req_123"
        }
        
        detected = self.detector.detect_sensitive_fields(log_entry)
        
        assert len(detected) == 1
        assert detected[0].field_name == "user_email"
        assert detected[0].field_type == "email"
        assert detected[0].confidence >= 0.8
    
    def test_phone_detection(self):
        """Test phone number pattern detection."""
        log_entry = {
            "phone": "555-123-4567",
            "timestamp": "2025-05-16T10:30:00Z"
        }
        
        detected = self.detector.detect_sensitive_fields(log_entry)
        
        assert len(detected) == 1
        assert detected[0].field_name == "phone"
        assert detected[0].field_type == "phone"
    
    def test_field_name_detection(self):
        """Test detection based on field names."""
        log_entry = {
            "password": "secret123",
            "api_key": "sk_live_abcd1234"
        }
        
        detected = self.detector.detect_sensitive_fields(log_entry)
        
        assert len(detected) == 2
        field_names = [d.field_name for d in detected]
        assert "password" in field_names
        assert "api_key" in field_names
    
    def test_no_detection(self):
        """Test logs with no sensitive fields."""
        log_entry = {
            "request_id": "req_123",
            "timestamp": "2025-05-16T10:30:00Z",
            "status_code": 200
        }
        
        detected = self.detector.detect_sensitive_fields(log_entry)
        
        assert len(detected) == 0
    
    def test_multiple_patterns(self):
        """Test detection of multiple patterns in one log."""
        log_entry = {
            "user_email": "test@example.com",
            "phone": "555-987-6543",
            "ssn": "123-45-6789",
            "request_id": "req_456"
        }
        
        detected = self.detector.detect_sensitive_fields(log_entry)
        
        assert len(detected) == 3
        detected_types = [d.field_type for d in detected]
        assert "email" in detected_types
        assert "phone" in detected_types
        assert "ssn" in detected_types
