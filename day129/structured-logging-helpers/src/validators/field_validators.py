"""Field validation system for structured logging."""
from typing import Dict, Any, Union, List
from datetime import datetime
import re


class FieldValidator:
    """Base class for field validators."""
    
    def validate(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize fields."""
        raise NotImplementedError


class TypeValidator(FieldValidator):
    """Validates field types and converts when possible."""
    
    def __init__(self):
        self.type_rules = {
            'user_id': int,
            'amount': float,
            'email': str,
            'timestamp': str,
            'success': bool,
            'response_time': float,
            'status_code': int
        }
        
    def validate(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert field types."""
        validated = fields.copy()
        
        for field_name, field_value in fields.items():
            if field_name in self.type_rules:
                expected_type = self.type_rules[field_name]
                try:
                    validated[field_name] = expected_type(field_value)
                except (ValueError, TypeError):
                    validated[f"{field_name}_validation_error"] = f"Expected {expected_type.__name__}, got {type(field_value).__name__}"
                    
        return validated


class RequiredFieldsValidator(FieldValidator):
    """Ensures required fields are present."""
    
    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields
        
    def validate(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Check for required fields."""
        validated = fields.copy()
        missing_fields = []
        
        for field in self.required_fields:
            if field not in fields or fields[field] is None:
                missing_fields.append(field)
                
        if missing_fields:
            validated['missing_required_fields'] = missing_fields
            
        return validated


class EmailValidator(FieldValidator):
    """Validates email field format."""
    
    def __init__(self):
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
    def validate(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate email format."""
        validated = fields.copy()
        
        if 'email' in fields:
            email = fields['email']
            if isinstance(email, str) and not self.email_pattern.match(email):
                validated['email_validation_error'] = "Invalid email format"
                
        return validated


class RangeValidator(FieldValidator):
    """Validates numeric fields are within acceptable ranges."""
    
    def __init__(self):
        self.range_rules = {
            'amount': (0, 1000000),  # $0 to $1M
            'response_time': (0, 30),  # 0 to 30 seconds
            'status_code': (100, 599),  # HTTP status codes
            'age': (0, 150)  # Human age limits
        }
        
    def validate(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate numeric ranges."""
        validated = fields.copy()
        
        for field_name, field_value in fields.items():
            if field_name in self.range_rules:
                min_val, max_val = self.range_rules[field_name]
                try:
                    numeric_value = float(field_value)
                    if not (min_val <= numeric_value <= max_val):
                        validated[f"{field_name}_range_error"] = f"Value {numeric_value} outside range [{min_val}, {max_val}]"
                except (ValueError, TypeError):
                    validated[f"{field_name}_type_error"] = f"Could not convert to numeric: {field_value}"
                    
        return validated


# Validator factory for easy setup
class ValidatorFactory:
    """Factory for creating common validator combinations."""
    
    @staticmethod
    def create_web_api_validators() -> List[FieldValidator]:
        """Create validators for web API logging."""
        return [
            TypeValidator(),
            RequiredFieldsValidator(['trace_id']),
            EmailValidator(),
            RangeValidator()
        ]
        
    @staticmethod
    def create_payment_validators() -> List[FieldValidator]:
        """Create validators for payment processing logs."""
        return [
            TypeValidator(),
            RequiredFieldsValidator(['user_id', 'amount', 'transaction_id']),
            RangeValidator()
        ]
        
    @staticmethod
    def create_user_activity_validators() -> List[FieldValidator]:
        """Create validators for user activity logs."""
        return [
            TypeValidator(),
            RequiredFieldsValidator(['user_id', 'action']),
            EmailValidator()
        ]
