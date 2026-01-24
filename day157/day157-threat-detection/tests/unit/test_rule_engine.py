import pytest
from src.engine.rule_engine import RuleEngine
from src.models import DetectionRule, LogEntry, SeverityLevel, ThreatCategory

@pytest.mark.asyncio
async def test_rule_evaluation():
    """Test rule engine evaluation"""
    rules = [
        DetectionRule(
            name="SQL Injection",
            pattern="(?i)union.*select",
            severity=SeverityLevel.HIGH,
            category=ThreatCategory.WEB_ATTACK,
            action="block"
        )
    ]
    
    engine = RuleEngine(rules)
    
    malicious_log = LogEntry(
        source_ip="192.168.1.100",
        endpoint="/api/users",
        method="GET",
        payload="' UNION SELECT password FROM users"
    )
    
    detections = await engine.evaluate(malicious_log)
    
    assert len(detections) > 0
    assert detections[0].severity == SeverityLevel.HIGH
    assert detections[0].rule_name == "SQL Injection"

@pytest.mark.asyncio
async def test_multiple_rule_evaluation():
    """Test evaluation against multiple rules"""
    rules = [
        DetectionRule(
            name="SQL Injection",
            pattern="(?i)union.*select",
            severity=SeverityLevel.HIGH,
            category=ThreatCategory.WEB_ATTACK,
            action="block"
        ),
        DetectionRule(
            name="XSS",
            pattern="(?i)<script",
            severity=SeverityLevel.HIGH,
            category=ThreatCategory.WEB_ATTACK,
            action="block"
        )
    ]
    
    engine = RuleEngine(rules)
    
    # Log with XSS
    xss_log = LogEntry(
        source_ip="10.0.0.1",
        endpoint="/comment",
        method="POST",
        payload="<script>alert('test')</script>"
    )
    
    detections = await engine.evaluate(xss_log)
    assert len(detections) == 1
    assert detections[0].rule_name == "XSS"
