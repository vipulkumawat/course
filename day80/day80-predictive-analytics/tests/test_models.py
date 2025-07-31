import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.arima_model import ARIMAModel
from src.models.prophet_model import ProphetModel
from src.models.exponential_smoothing import ExponentialSmoothingModel
from src.models.lstm_model import LSTMModel

class TestForecastingModels:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample time series data for testing"""
        dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='5T')
        values = 50 + 10 * np.sin(np.arange(len(dates)) * 2 * np.pi / 288) + np.random.normal(0, 5, len(dates))
        
        X = pd.DataFrame({'timestamp': dates})
        X.set_index('timestamp', inplace=True)
        y = pd.Series(values, index=dates, name='response_time')
        
        return X, y
    
    def test_arima_model(self, sample_data):
        """Test ARIMA model training and prediction"""
        X, y = sample_data
        
        model = ARIMAModel(order=(1, 1, 1))
        model.fit(X, y)
        
        assert model.is_fitted
        
        predictions, confidence = model.predict(steps=12)
        assert len(predictions) == 12
        assert len(confidence) == 12
        assert all(0 <= c <= 1 for c in confidence)
    
    def test_prophet_model(self, sample_data):
        """Test Prophet model training and prediction"""
        X, y = sample_data
        
        model = ProphetModel()
        model.fit(X, y)
        
        assert model.is_fitted
        
        predictions, confidence = model.predict(steps=12)
        assert len(predictions) == 12
        assert len(confidence) == 12
    
    def test_exponential_smoothing_model(self, sample_data):
        """Test Exponential Smoothing model"""
        X, y = sample_data
        
        model = ExponentialSmoothingModel()
        model.fit(X, y)
        
        assert model.is_fitted
        
        predictions, confidence = model.predict(steps=12)
        assert len(predictions) == 12
        assert len(confidence) == 12
    
    def test_lstm_model(self, sample_data):
        """Test LSTM model (simplified test due to complexity)"""
        X, y = sample_data
        
        # Use smaller dataset for LSTM test
        X_small = X.tail(200)
        y_small = y.tail(200)
        
        model = LSTMModel(sequence_length=20, epochs=2)  # Reduced for testing
        model.fit(X_small, y_small)
        
        assert model.is_fitted
        
        predictions, confidence = model.predict(steps=5)
        assert len(predictions) == 5
        assert len(confidence) == 5
    
    def test_model_validation(self, sample_data):
        """Test model validation functionality"""
        X, y = sample_data
        
        # Split data
        split_idx = int(len(y) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        model = ARIMAModel()
        model.fit(X_train, y_train)
        
        metrics = model.validate(X_val, y_val)
        
        assert 'mae' in metrics
        assert 'mse' in metrics
        assert 'rmse' in metrics
        assert 'accuracy' in metrics
        assert metrics['accuracy'] >= 0
