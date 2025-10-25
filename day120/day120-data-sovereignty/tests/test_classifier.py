"""Tests for data classifier"""
import pytest
import sys
sys.path.append('../src')

from classification.classifier import DataClassifier, DataSensitivity

def test_pii_detection():
    classifier = DataClassifier()
    
    log_with_email = {
        'id': 'test1',
        'message': 'User john@example.com logged in',
        'ip_address': '192.168.1.1'
    }
    
    classification = classifier.classify_log(log_with_email)
    assert classification['contains_pii'] == True

def test_sensitivity_classification():
    classifier = DataClassifier()
    
    log_with_password = {
        'id': 'test2',
        'message': 'Password reset requested',
        'ip_address': '192.168.1.1'
    }
    
    classification = classifier.classify_log(log_with_password)
    assert classification['sensitivity'] == DataSensitivity.RESTRICTED.value

def test_location_extraction():
    classifier = DataClassifier()
    
    log_with_location = {
        'id': 'test3',
        'message': 'Test log',
        'user_location': 'EU'
    }
    
    classification = classifier.classify_log(log_with_location)
    assert classification['data_subject_location'] == 'EU'

def test_gdpr_regulations():
    classifier = DataClassifier()
    
    eu_log = {
        'id': 'test4',
        'message': 'EU user activity',
        'user_location': 'EU'
    }
    
    classification = classifier.classify_log(eu_log)
    assert 'gdpr' in classification['applicable_regulations']
