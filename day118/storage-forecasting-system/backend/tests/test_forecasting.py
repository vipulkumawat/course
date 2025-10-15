import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from forecasting.engine import ForecastingEngine
from collectors.metrics_collector import StorageMetricsCollector
from utils.cost_calculator import StorageCostCalculator

class TestForecastingEngine:
    def setup_method(self):
        self.engine = ForecastingEngine()
        self.collector = StorageMetricsCollector()
        
    def test_forecasting_engine_initialization(self):
        """Test that forecasting engine initializes correctly"""
        assert self.engine is not None
        assert 'linear' in self.engine.models
        assert 'random_forest' in self.engine.models
        
    def test_generate_forecast_with_minimal_data(self):
        """Test forecasting with minimal historical data"""
        # Generate test data
        historical_data = self.collector.generate_historical_data(days=30)
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Generate forecast
        result = self.engine.generate_ensemble_forecast(df, horizon_days=7)
        
        assert 'forecast' in result
        assert 'lower_bound' in result
        assert 'upper_bound' in result
        assert len(result['forecast']) == 7
        assert result['model_accuracy'] >= 0
        
    def test_prepare_features(self):
        """Test feature preparation"""
        historical_data = self.collector.generate_historical_data(days=60)
        df = pd.DataFrame(historical_data)
        
        X, y, timestamps = self.engine.prepare_features(df)
        
        assert len(X) > 0
        assert len(y) > 0
        assert len(X) == len(y)
        assert 'hour' in X.columns
        assert 'day_of_week' in X.columns

class TestStorageMetricsCollector:
    def setup_method(self):
        self.collector = StorageMetricsCollector("test-node", "test-tenant")
        
    def test_collector_initialization(self):
        """Test collector initializes with correct parameters"""
        assert self.collector.node_id == "test-node"
        assert self.collector.tenant_id == "test-tenant"
        
    def test_generate_historical_data(self):
        """Test historical data generation"""
        data = self.collector.generate_historical_data(days=30)
        
        assert len(data) > 0
        assert all('timestamp' in item for item in data)
        assert all('used_bytes' in item for item in data)
        assert all('node_id' in item for item in data)
        
    @pytest.mark.asyncio
    async def test_collect_current_metrics(self):
        """Test current metrics collection"""
        metrics = await self.collector.collect_current_metrics()
        
        assert 'timestamp' in metrics
        assert 'node_id' in metrics
        assert 'used_bytes' in metrics
        assert 'total_bytes' in metrics
        assert metrics['used_bytes'] > 0

class TestStorageCostCalculator:
    def setup_method(self):
        self.calculator = StorageCostCalculator()
        
    def test_monthly_cost_calculation(self):
        """Test monthly cost calculation"""
        cost = self.calculator.calculate_monthly_cost(100.0, 'primary')
        assert cost > 0
        assert cost == 100.0 * 0.023  # default primary cost
        
    def test_forecast_cost_calculation(self):
        """Test forecast cost calculation"""
        forecast_data = {
            'forecast': [100 * 1024**3, 110 * 1024**3, 120 * 1024**3],  # 100GB, 110GB, 120GB in bytes
            'dates': ['2025-06-01', '2025-06-02', '2025-06-03']
        }
        
        cost_result = self.calculator.calculate_forecast_costs(forecast_data)
        
        assert 'daily_costs' in cost_result
        assert 'monthly_costs' in cost_result
        assert 'total_period_cost' in cost_result
        assert len(cost_result['daily_costs']) == 3
        
    def test_cost_scenarios(self):
        """Test cost scenario generation"""
        scenarios = self.calculator.generate_cost_scenarios(100.0, [0.01, 0.02, 0.05])
        
        assert len(scenarios) == 3
        assert '1.0%_growth' in scenarios
        assert '2.0%_growth' in scenarios
        assert '5.0%_growth' in scenarios
        
        for scenario in scenarios.values():
            assert 'monthly_usage_gb' in scenario
            assert 'monthly_costs' in scenario
            assert 'total_annual_cost' in scenario

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
