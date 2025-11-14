"""Core structured logging helper with validation and context injection."""
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    message: str
    level: LogLevel
    timestamp: str
    service_name: str
    trace_id: str
    fields: Dict[str, Any]
    context: Dict[str, Any]


class StructuredLogger:
    """High-performance structured logger with validation and context injection."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.context_providers = []
        self.validators = []
        self.serialization_cache = {}
        
    def add_context_provider(self, provider):
        """Add automatic context injection."""
        self.context_providers.append(provider)
        
    def add_validator(self, validator):
        """Add field validation."""
        self.validators.append(validator)
        
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID."""
        return str(uuid.uuid4())
        
    def _inject_context(self) -> Dict[str, Any]:
        """Inject context from all providers."""
        context = {}
        for provider in self.context_providers:
            try:
                provider_context = provider.get_context()
                context.update(provider_context)
            except Exception as e:
                # Context injection should never break logging
                context['context_error'] = str(e)
        return context
        
    def _validate_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize fields."""
        validated_fields = fields.copy()
        
        for validator in self.validators:
            try:
                validated_fields = validator.validate(validated_fields)
            except Exception as e:
                # Add validation error but don't fail
                validated_fields['validation_error'] = str(e)
                
        return validated_fields
        
    def _create_log_entry(self, level: LogLevel, message: str, **fields) -> LogEntry:
        """Create structured log entry with all processing."""
        timestamp = datetime.now(timezone.utc).isoformat()
        trace_id = fields.pop('trace_id', self._generate_trace_id())
        
        # Process fields through validators
        validated_fields = self._validate_fields(fields)
        
        # Inject context
        context = self._inject_context()
        
        return LogEntry(
            message=message,
            level=level,
            timestamp=timestamp,
            service_name=self.service_name,
            trace_id=trace_id,
            fields=validated_fields,
            context=context
        )
        
    def debug(self, message: str, **fields):
        """Log debug message."""
        return self._log(LogLevel.DEBUG, message, **fields)
        
    def info(self, message: str, **fields):
        """Log info message."""
        return self._log(LogLevel.INFO, message, **fields)
        
    def warning(self, message: str, **fields):
        """Log warning message."""
        return self._log(LogLevel.WARNING, message, **fields)
        
    def error(self, message: str, **fields):
        """Log error message."""
        return self._log(LogLevel.ERROR, message, **fields)
        
    def critical(self, message: str, **fields):
        """Log critical message."""
        return self._log(LogLevel.CRITICAL, message, **fields)
        
    def _log(self, level: LogLevel, message: str, **fields) -> LogEntry:
        """Internal logging method."""
        entry = self._create_log_entry(level, message, **fields)
        
        # Convert to JSON for output
        entry_dict = asdict(entry)
        entry_dict['level'] = entry.level.value
        
        # Print structured JSON
        print(json.dumps(entry_dict, indent=2))
        
        return entry


# Performance-optimized JSON serializer
class FastJSONSerializer:
    """High-performance JSON serialization for structured logs."""
    
    def __init__(self):
        self.template_cache = {}
        
    def serialize(self, log_entry: LogEntry) -> str:
        """Serialize log entry to JSON with caching optimization."""
        entry_dict = asdict(log_entry)
        entry_dict['level'] = log_entry.level.value
        
        # Use template caching for common log structures
        template_key = self._get_template_key(entry_dict)
        
        if template_key in self.template_cache:
            template = self.template_cache[template_key]
            return self._fill_template(template, entry_dict)
        else:
            json_str = json.dumps(entry_dict, separators=(',', ':'))
            self.template_cache[template_key] = json_str
            return json_str
            
    def _get_template_key(self, entry_dict: Dict) -> str:
        """Generate cache key for log structure."""
        field_keys = sorted(entry_dict.get('fields', {}).keys())
        context_keys = sorted(entry_dict.get('context', {}).keys())
        return f"{entry_dict['level']}:{','.join(field_keys)}:{','.join(context_keys)}"
        
    def _fill_template(self, template: str, data: Dict) -> str:
        """Fill template with actual data (simplified version)."""
        return json.dumps(data, separators=(',', ':'))
