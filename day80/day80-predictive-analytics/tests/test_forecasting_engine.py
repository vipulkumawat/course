import pytest
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.forecasting.engine import ForecastingEngine

class TestForecastingEngine:
    
    def test_engine_initialization(self):
        """Test forecasting engine initialization"""
        engine = ForecastingEngine()
        
        # Should have models dict (may be empty if no trained models)
        assert hasattr(engine, 'models')
        assert isinstance(engine.models, dict)
        assert hasattr(engine, 'ensemble_weights')
    
    def test_generate_forecast(self):
        """Test forecast generation"""
        engine = ForecastingEngine()
        
        # Generate forecast (should work even with no models via fallback)
        forecast = engine.generate_forecast(steps=12)
        
        assert 'timestamp' in forecast
        assert 'forecast_horizon_minutes' in forecast
        assert 'ensemble_prediction' in forecast
        assert 'ensemble_confidence' in forecast
        assert 'timestamps' in forecast
        assert 'alert_level' in forecast
        
        assert len(forecast['ensemble_prediction']) == 12
        assert len(forecast['ensemble_confidence']) == 12
        assert len(forecast['timestamps']) == 12
    
    def test_alert_level_calculation(self):
        """Test alert level calculation logic"""
        engine = ForecastingEngine()
        
        # Test high confidence
        high_conf = np.array([0.9, 0.85, 0.88, 0.92])
        alert_level = engine._calculate_alert_level(high_conf)
        assert alert_level == "high"
        
        # Test medium confidence
        med_conf = np.array([0.7, 0.65, 0.75, 0.68])
        alert_level = engine._calculate_alert_level(med_conf)
        assert alert_level == "medium"
        
        # Test low confidence
        low_conf = np.array([0.4, 0.5, 0.3, 0.6])
        alert_level = engine._calculate_alert_level(low_conf)
        assert alert_level == "low"
