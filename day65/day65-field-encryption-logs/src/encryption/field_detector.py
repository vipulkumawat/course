import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from config.encryption_config import config
import logging

@dataclass
class DetectedField:
    field_name: str
    field_value: str
    field_type: str
    confidence: float
    pattern_matched: str = None

class FieldDetector:
    """Detects sensitive fields in log entries using patterns and field names."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in config.sensitive_patterns.items()
        }
        
    def detect_sensitive_fields(self, log_entry: Dict[str, Any]) -> List[DetectedField]:
        """Detect all sensitive fields in a log entry."""
        detected_fields = []
        
        for field_name, field_value in log_entry.items():
            if not isinstance(field_value, str):
                continue
                
            # Check field name patterns
            field_detection = self._check_field_name(field_name, field_value)
            if field_detection:
                detected_fields.append(field_detection)
                continue
                
            # Check value patterns
            value_detection = self._check_value_patterns(field_name, field_value)
            if value_detection:
                detected_fields.append(value_detection)
                
        return detected_fields
    
    def _check_field_name(self, field_name: str, field_value: str) -> DetectedField:
        """Check if field name indicates sensitive data."""
        field_lower = field_name.lower()
        
        for sensitive_name in config.sensitive_field_names:
            if sensitive_name in field_lower:
                return DetectedField(
                    field_name=field_name,
                    field_value=field_value,
                    field_type=sensitive_name,
                    confidence=0.9
                )
        return None
    
    def _check_value_patterns(self, field_name: str, field_value: str) -> DetectedField:
        """Check if field value matches sensitive patterns."""
        for pattern_name, compiled_pattern in self.compiled_patterns.items():
            if compiled_pattern.search(field_value):
                return DetectedField(
                    field_name=field_name,
                    field_value=field_value,
                    field_type=pattern_name,
                    confidence=0.8,
                    pattern_matched=pattern_name
                )
        return None
    
    def get_detection_stats(self) -> Dict[str, int]:
        """Get statistics about field detection."""
        return {
            'total_patterns': len(self.compiled_patterns),
            'sensitive_field_names': len(config.sensitive_field_names)
        }
