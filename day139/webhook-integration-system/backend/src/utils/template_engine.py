import json
from typing import Dict, Any
from datetime import datetime
import re

class TemplateEngine:
    """Simple template engine for webhook payload transformation"""
    
    def transform(self, event_data: Dict, template: str = None) -> Dict[str, Any]:
        """Transform event data using template or default format"""
        if not template:
            return self._default_transform(event_data)
        
        try:
            template_dict = json.loads(template)
            return self._apply_template(event_data, template_dict)
        except json.JSONDecodeError:
            # Fallback to default transformation
            return self._default_transform(event_data)
    
    def _default_transform(self, event_data: Dict) -> Dict[str, Any]:
        """Default webhook payload format"""
        return {
            "event_type": event_data.get("type", "log_event"),
            "timestamp": event_data.get("timestamp", datetime.utcnow().isoformat()),
            "severity": event_data.get("level", "info"),
            "message": event_data.get("message", ""),
            "source": event_data.get("source", "log_processor"),
            "metadata": event_data.get("metadata", {}),
            "webhook_id": event_data.get("event_id", ""),
            "system": "Distributed Log Processing System"
        }
    
    def _apply_template(self, event_data: Dict, template: Dict) -> Dict[str, Any]:
        """Apply template transformations"""
        result = {}
        
        for key, value in template.items():
            if isinstance(value, str):
                # Process template strings with placeholders
                result[key] = self._process_template_string(value, event_data)
            elif isinstance(value, dict):
                # Recursive processing for nested objects
                result[key] = self._apply_template(event_data, value)
            elif isinstance(value, list):
                # Process list templates
                result[key] = [self._apply_template(event_data, item) if isinstance(item, dict) 
                              else self._process_template_string(str(item), event_data) 
                              for item in value]
            else:
                result[key] = value
                
        return result
    
    def _process_template_string(self, template_str: str, event_data: Dict) -> Any:
        """Process template string with variable substitution"""
        # Find all {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            value = self._get_nested_value(event_data, var_path)
            return str(value) if value is not None else ""
        
        return re.sub(pattern, replace_var, template_str)
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
                
        return current
