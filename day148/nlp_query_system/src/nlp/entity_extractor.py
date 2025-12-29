import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dateutil import parser as date_parser

class EntityExtractor:
    """Extracts entities from natural language queries"""
    
    def __init__(self, schema_fields: List[str]):
        self.schema_fields = schema_fields
        self.log_levels = ['error', 'warn', 'warning', 'info', 'debug']
        
        # Time expression patterns
        self.time_patterns = {
            'last_x_minutes': r'last\s+(\d+)\s+minutes?',
            'last_x_hours': r'last\s+(\d+)\s+hours?',
            'last_x_days': r'last\s+(\d+)\s+days?',
            'today': r'today',
            'yesterday': r'yesterday',
            'between': r'between\s+(.+?)\s+and\s+(.+?)(?:\s|$)'
        }
    
    def extract(self, query: str) -> Dict[str, any]:
        """Extract all entities from query"""
        entities = {
            'time_range': self._extract_time_range(query),
            'log_level': self._extract_log_level(query),
            'service': self._extract_service(query),
            'fields': self._extract_fields(query),
            'values': self._extract_values(query)
        }
        
        return {k: v for k, v in entities.items() if v is not None}
    
    def _extract_time_range(self, query: str) -> Optional[Dict[str, datetime]]:
        """Extract time range from query"""
        query_lower = query.lower()
        now = datetime.now()
        
        # Check for "last X minutes/hours/days"
        for pattern_name, pattern in self.time_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                if pattern_name == 'last_x_minutes':
                    minutes = int(match.group(1))
                    return {
                        'start': now - timedelta(minutes=minutes),
                        'end': now
                    }
                elif pattern_name == 'last_x_hours':
                    hours = int(match.group(1))
                    return {
                        'start': now - timedelta(hours=hours),
                        'end': now
                    }
                elif pattern_name == 'last_x_days':
                    days = int(match.group(1))
                    return {
                        'start': now - timedelta(days=days),
                        'end': now
                    }
                elif pattern_name == 'today':
                    return {
                        'start': now.replace(hour=0, minute=0, second=0),
                        'end': now
                    }
                elif pattern_name == 'yesterday':
                    yesterday = now - timedelta(days=1)
                    return {
                        'start': yesterday.replace(hour=0, minute=0, second=0),
                        'end': yesterday.replace(hour=23, minute=59, second=59)
                    }
                elif pattern_name == 'between':
                    try:
                        start_str, end_str = match.group(1), match.group(2)
                        return {
                            'start': date_parser.parse(start_str),
                            'end': date_parser.parse(end_str)
                        }
                    except:
                        pass
        
        # Return None if no time expression found - don't apply default time filter
        return None
    
    def _extract_log_level(self, query: str) -> Optional[str]:
        """Extract log level from query"""
        query_lower = query.lower()
        for level in self.log_levels:
            if level in query_lower:
                # Normalize warnings to warn
                if level == 'warning':
                    return 'warn'
                return level
        return None
    
    def _extract_service(self, query: str) -> Optional[str]:
        """Extract service name from query"""
        # Common service name patterns
        service_pattern = r'(?:from|in|for)\s+(?:the\s+)?([a-z_-]+)\s+(?:service|api|system)'
        match = re.search(service_pattern, query.lower())
        if match:
            return match.group(1)
        return None
    
    def _extract_fields(self, query: str) -> List[str]:
        """Extract field names mentioned in query"""
        mentioned_fields = []
        query_lower = query.lower()
        
        for field in self.schema_fields:
            if field.lower() in query_lower:
                mentioned_fields.append(field)
        
        return mentioned_fields if mentioned_fields else []
    
    def _extract_values(self, query: str) -> Dict[str, str]:
        """Extract field values from query"""
        values = {}
        
        # Extract quoted strings as values
        quoted_pattern = r'["\']([^"\']+)["\']'
        matches = re.findall(quoted_pattern, query)
        if matches:
            values['_quoted'] = matches
        
        # Extract numeric values (but exclude time-related numbers)
        numeric_pattern = r'\b(\d+)\b'
        numbers = re.findall(numeric_pattern, query)
        # Filter out time-related numbers (minutes, hours, days)
        time_keywords = ['minute', 'hour', 'day', 'second', 'week', 'month', 'year']
        query_lower = query.lower()
        filtered_numbers = []
        for num in numbers:
            # Check if this number is part of a time expression
            num_pos = query_lower.find(num)
            if num_pos != -1:
                context = query_lower[max(0, num_pos-20):num_pos+20]
                is_time_number = any(kw in context for kw in time_keywords)
                if not is_time_number:
                    filtered_numbers.append(int(num))
        if filtered_numbers:
            values['_numbers'] = filtered_numbers
        
        # Extract meaningful search terms (words that aren't common stop words or query keywords)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 
            'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 
            'show', 'me', 'find', 'get', 'display', 'list', 'view', 'logs', 
            'log', 'error', 'warn', 'info', 'debug', 'service', 'api', 'system'
        }
        
        # Extract words that are likely search terms
        words = re.findall(r'\b[a-z]{3,}\b', query.lower())
        search_terms = [w for w in words if w not in stop_words and w not in self.log_levels]
        
        # Also check if any schema fields are mentioned, and extract values near them
        if search_terms:
            values['_search_terms'] = search_terms[:5]  # Limit to 5 terms
        
        return values
