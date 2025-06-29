"""Tests for pattern matching engine."""
import pytest
import asyncio
from src.pattern_matching.engine import PatternMatcher
from config.database import LogEntry

@pytest.fixture
def pattern_matcher():
    return PatternMatcher()

@pytest.mark.asyncio
async def test_auth_failure_pattern(pattern_matcher):
    """Test authentication failure pattern detection."""
    log_entry = LogEntry(
        message="Authentication failed for user admin",
        level="ERROR",
        source="auth_service"
    )
    
    matches = await pattern_matcher.analyze_log(log_entry)
    assert len(matches) == 1
    assert matches[0]['pattern_name'] == 'auth_failure'
    assert matches[0]['severity'] == 'high'

@pytest.mark.asyncio
async def test_database_error_pattern(pattern_matcher):
    """Test database error pattern detection."""
    log_entry = LogEntry(
        message="Database connection timeout occurred",
        level="ERROR",
        source="db_service"
    )
    
    matches = await pattern_matcher.analyze_log(log_entry)
    assert len(matches) == 1
    assert matches[0]['pattern_name'] == 'database_error'

@pytest.mark.asyncio
async def test_no_pattern_match(pattern_matcher):
    """Test log that doesn't match any pattern."""
    log_entry = LogEntry(
        message="User logged in successfully",
        level="INFO",
        source="auth_service"
    )
    
    matches = await pattern_matcher.analyze_log(log_entry)
    assert len(matches) == 0

def test_add_custom_pattern(pattern_matcher):
    """Test adding custom pattern."""
    pattern_matcher.add_pattern(
        name="custom_test",
        pattern=r"test\s+error",
        threshold=2,
        window=60,
        severity="medium"
    )
    
    assert "custom_test" in pattern_matcher.patterns
    assert pattern_matcher.patterns["custom_test"]["threshold"] == 2
