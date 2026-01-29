"""Test UBA components"""
import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_extraction.feature_engine import FeatureEngine
from feature_extraction.baseline_manager import BaselineManager
from detection.zscore_detector import ZScoreDetector
from detection.temporal_detector import TemporalDetector
from detection.ensemble_scorer import EnsembleScorer
from datetime import datetime

def test_feature_extraction():
    """Test feature extraction from events"""
    engine = FeatureEngine()
    
    # Add some events
    user = "test_user"
    event = {
        'timestamp': datetime.now().isoformat(),
        'event_type': 'login',
        'user': user,
        'details': {}
    }
    
    engine.add_event(user, event)
    features = engine.extract_features(user, event)
    
    assert isinstance(features, dict)
    assert 'login_frequency' in features
    assert 'time_of_day_score' in features

def test_baseline_manager():
    """Test baseline learning"""
    manager = BaselineManager()
    
    user = "test_user"
    features = {
        'login_frequency': 5.0,
        'access_count': 20.0
    }
    
    manager.update_baseline(user, features)
    baseline = manager.get_baseline(user)
    
    assert baseline['sample_count'] == 1
    assert baseline['mean']['login_frequency'] == 5.0

def test_zscore_detector():
    """Test Z-score anomaly detection"""
    detector = ZScoreDetector(threshold=3.0)
    
    baseline = {
        'mean': {'access_count': 50.0},
        'std': {'access_count': 10.0}
    }
    
    # Normal value
    normal_features = {'access_count': 52.0}
    score, anomalies = detector.detect(normal_features, baseline)
    assert score < 50
    
    # Anomalous value
    anomalous_features = {'access_count': 200.0}
    score, anomalies = detector.detect(anomalous_features, baseline)
    assert score > 50

def test_temporal_detector():
    """Test temporal pattern detection"""
    detector = TemporalDetector()
    
    user = "test_user"
    
    # Learn normal pattern (business hours)
    for hour in range(9, 18):
        for _ in range(10):
            dt = datetime.now().replace(hour=hour)
            detector.learn_pattern(user, dt.isoformat())
    
    # Test normal time
    normal_time = datetime.now().replace(hour=10).isoformat()
    score, reasons = detector.detect(user, normal_time)
    assert score < 50
    
    # Test anomalous time (3 AM)
    anomalous_time = datetime.now().replace(hour=3).isoformat()
    score, reasons = detector.detect(user, anomalous_time)
    assert score > 50

def test_ensemble_scorer():
    """Test ensemble scoring"""
    scorer = EnsembleScorer()
    
    detector_scores = {
        'zscore': (75.0, ['high access_count']),
        'temporal': (60.0, ['unusual hour'])
    }
    
    result = scorer.compute_score(detector_scores)
    
    assert 'final_score' in result
    assert 'risk_level' in result
    assert result['final_score'] > 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
