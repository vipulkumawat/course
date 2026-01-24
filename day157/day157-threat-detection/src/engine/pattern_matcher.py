import re
from typing import List, Dict, Optional, Tuple
from src.models import DetectionRule, LogEntry
import structlog

logger = structlog.get_logger()

class PatternMatcher:
    def __init__(self):
        self.compiled_patterns: Dict[str, re.Pattern] = {}
        self.match_count = 0
        
    def compile_rules(self, rules: List[DetectionRule]) -> None:
        """Compile regex patterns for performance"""
        for rule in rules:
            try:
                self.compiled_patterns[rule.name] = re.compile(
                    rule.pattern,
                    re.IGNORECASE | re.MULTILINE
                )
                logger.info("compiled_rule", rule_name=rule.name)
            except re.error as e:
                logger.error("pattern_compile_failed", rule=rule.name, error=str(e))
    
    def match(self, log_entry: LogEntry, rule: DetectionRule) -> Optional[Tuple[bool, str]]:
        """Match log entry against a specific rule"""
        if rule.name not in self.compiled_patterns:
            return None
        
        pattern = self.compiled_patterns[rule.name]
        
        # Search in payload, endpoint, and user_agent
        search_fields = [
            log_entry.payload,
            log_entry.endpoint,
            log_entry.user_agent or ""
        ]
        
        for field in search_fields:
            match = pattern.search(field)
            if match:
                self.match_count += 1
                return True, match.group(0)
        
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get matcher statistics"""
        return {
            "total_matches": self.match_count,
            "compiled_patterns": len(self.compiled_patterns)
        }
