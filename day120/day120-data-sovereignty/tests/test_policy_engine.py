"""Tests for policy enforcement engine"""
import pytest
import sys
sys.path.append('../src')

from enforcement.policy_engine import PolicyEngine, EnforcementAction

def test_eu_storage_validation():
    engine = PolicyEngine()
    
    classification = {
        'data_subject_location': 'EU',
        'contains_pii': True,
        'required_encryption': True
    }
    
    decision = engine.validate_storage(classification, 'eu-west-1')
    assert decision['allowed'] == True

def test_prohibited_storage():
    engine = PolicyEngine()
    
    classification = {
        'data_subject_location': 'CN',
        'contains_pii': False,
        'required_encryption': False
    }
    
    decision = engine.validate_storage(classification, 'eu-west-1')
    assert decision['allowed'] == False

def test_cross_border_transfer_denial():
    engine = PolicyEngine()
    
    classification = {
        'data_subject_location': 'EU',
        'contains_pii': True
    }
    
    decision = engine.validate_transfer(classification, 'eu-west-1', 'us-east-1')
    # Should allow with anonymization
    assert decision['action'] in [EnforcementAction.ANONYMIZE.value, EnforcementAction.DENY.value]

def test_allowed_transfer():
    engine = PolicyEngine()
    
    classification = {
        'data_subject_location': 'US',
        'contains_pii': False
    }
    
    decision = engine.validate_transfer(classification, 'us-east-1', 'us-west-2')
    assert decision['allowed'] == True
