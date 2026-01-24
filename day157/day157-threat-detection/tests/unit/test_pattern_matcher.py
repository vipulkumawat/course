import pytest
from src.engine.pattern_matcher import PatternMatcher
from src.models import DetectionRule, LogEntry, SeverityLevel, ThreatCategory

def test_sql_injection_detection():
    """Test SQL injection pattern matching"""
    matcher = PatternMatcher()
    
    rule = DetectionRule(
        name="SQL Injection",
        pattern="(?i)(union.*select|drop.*table)",
        severity=SeverityLevel.HIGH,
        category=ThreatCategory.WEB_ATTACK,
        action="block"
    )
    
    matcher.compile_rules([rule])
    
    # Malicious log
    malicious_log = LogEntry(
        source_ip="192.168.1.100",
        endpoint="/api/users",
        method="GET",
        payload="' UNION SELECT * FROM users --"
    )
    
    result = matcher.match(malicious_log, rule)
    assert result is not None
    assert result[0] is True
    
    # Benign log
    benign_log = LogEntry(
        source_ip="192.168.1.100",
        endpoint="/api/users",
        method="GET",
        payload="user_id=123"
    )
    
    result = matcher.match(benign_log, rule)
    assert result is None

def test_xss_detection():
    """Test XSS pattern matching"""
    matcher = PatternMatcher()
    
    rule = DetectionRule(
        name="XSS Attack",
        pattern="(?i)(<script|javascript:|onerror=)",
        severity=SeverityLevel.HIGH,
        category=ThreatCategory.WEB_ATTACK,
        action="block"
    )
    
    matcher.compile_rules([rule])
    
    xss_log = LogEntry(
        source_ip="10.0.0.1",
        endpoint="/comment",
        method="POST",
        payload="<script>alert('XSS')</script>"
    )
    
    result = matcher.match(xss_log, rule)
    assert result is not None
    assert "script" in result[1].lower()
