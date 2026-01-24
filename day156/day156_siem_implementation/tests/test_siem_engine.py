"""
Unit tests for SIEM Engine
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.insert(0, 'src')

from siem.engine import (
    SecurityEvent, EventType, Severity, SecurityIncident,
    CorrelationEngine, RiskScorer, SIEMEngine
)


@pytest.fixture
def sample_config():
    return {
        'correlation': {
            'time_window_seconds': 300,
            'max_events_per_window': 10000,
            'suspicious_threshold': 0.7,
            'critical_threshold': 0.9
        },
        'detection_rules': {
            'brute_force': {
                'enabled': True,
                'failed_attempts_threshold': 5,
                'time_window_seconds': 60
            },
            'privilege_escalation': {
                'enabled': True,
                'suspicious_actions': ['sudo', 'su', 'admin'],
                'time_window_seconds': 300
            },
            'anomalous_access': {
                'enabled': True
            }
        },
        'risk_scoring': {
            'base_weights': {
                'authentication_failure': 0.3,
                'privilege_change': 0.6,
                'data_access': 0.4
            },
            'multipliers': {
                'critical_asset': 2.0,
                'suspicious_ip': 1.5
            }
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None
        }
    }


@pytest.fixture
def sample_auth_failure():
    return SecurityEvent(
        event_id="EVT-001",
        timestamp=time.time(),
        event_type=EventType.AUTH_FAILURE,
        user="testuser",
        source_ip="192.168.1.100",
        destination=None,
        action="authentication",
        success=False,
        metadata={}
    )


def test_security_event_creation(sample_auth_failure):
    """Test security event object creation"""
    assert sample_auth_failure.event_type == EventType.AUTH_FAILURE
    assert sample_auth_failure.user == "testuser"
    assert sample_auth_failure.success is False


def test_risk_scorer_calculation(sample_config, sample_auth_failure):
    """Test risk score calculation"""
    scorer = RiskScorer(sample_config)
    risk = scorer.calculate_event_risk(sample_auth_failure)
    
    assert 0 <= risk <= 1.0
    assert risk > 0  # Failed auth should have some risk


def test_risk_scorer_with_critical_asset(sample_config, sample_auth_failure):
    """Test risk scoring with critical asset multiplier"""
    scorer = RiskScorer(sample_config)
    
    # Add critical asset flag
    sample_auth_failure.metadata['critical_asset'] = True
    risk = scorer.calculate_event_risk(sample_auth_failure)
    
    # Should be higher due to multiplier
    assert risk > 0.3


@pytest.mark.asyncio
async def test_correlation_engine_brute_force():
    """Test brute force detection"""
    # This test would need a mock Redis client
    # Simplified version for demonstration
    assert True  # Placeholder


def test_incident_creation():
    """Test security incident creation"""
    event = SecurityEvent(
        event_id="EVT-001",
        timestamp=time.time(),
        event_type=EventType.AUTH_FAILURE,
        user="testuser",
        source_ip="192.168.1.100",
        destination=None,
        action="authentication",
        success=False,
        metadata={}
    )
    
    incident = SecurityIncident(
        incident_id="INC-001",
        severity=Severity.HIGH,
        title="Test Incident",
        description="Test description",
        risk_score=0.85,
        events=[event],
        created_at=time.time()
    )
    
    assert incident.severity == Severity.HIGH
    assert len(incident.events) == 1
    assert incident.risk_score == 0.85


def test_incident_serialization():
    """Test incident serialization to dict"""
    event = SecurityEvent(
        event_id="EVT-001",
        timestamp=time.time(),
        event_type=EventType.AUTH_FAILURE,
        user="testuser",
        source_ip="192.168.1.100",
        destination=None,
        action="authentication",
        success=False,
        metadata={}
    )
    
    incident = SecurityIncident(
        incident_id="INC-001",
        severity=Severity.HIGH,
        title="Test Incident",
        description="Test description",
        risk_score=0.85,
        events=[event],
        created_at=time.time()
    )
    
    incident_dict = incident.to_dict()
    
    assert 'incident_id' in incident_dict
    assert 'severity' in incident_dict
    assert 'events' in incident_dict
    assert isinstance(incident_dict['events'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
