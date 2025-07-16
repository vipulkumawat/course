import pytest
import re
from src.main import redact_log

def test_redact_log_email():
    log = "User john.doe@example.com logged in."
    redacted = redact_log(log)
    assert "[REDACTED_EMAIL]" in redacted
    assert "john.doe@example.com" not in redacted

def test_redact_log_credit_card():
    log = "Payment processed for card 4111 1111 1111 1111."
    redacted = redact_log(log)
    assert "[REDACTED_CREDIT_CARD]" in redacted
    assert "4111 1111 1111 1111" not in redacted

def test_redact_log_mixed():
    log = "Card 5500-0000-0000-0004 used by jane@doe.com."
    redacted = redact_log(log)
    assert "[REDACTED_CREDIT_CARD]" in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "5500-0000-0000-0004" not in redacted
    assert "jane@doe.com" not in redacted

def test_redact_log_no_sensitive():
    log = "No sensitive info here."
    redacted = redact_log(log)
    assert redacted == log 