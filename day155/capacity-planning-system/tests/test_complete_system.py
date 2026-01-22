"""
Comprehensive system tests for capacity planning
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from collectors.metrics_collector import MetricsCollector
from analyzers.time_series_analyzer import TimeSeriesAnalyzer
from analyzers.forecasting_engine import ForecastingEngine
from calculators.resource_calculator import ResourceCalculator


class TestMetricsCollector:
    def test_synthetic_data_generation(self):
        """Test synthetic data generation"""
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=30)
        
        assert len(df) == 30 * 24  # 30 days of hourly data
        assert 'logs_per_second' in df.columns
        assert df['logs_per_second'].min() > 0
        assert df['logs_per_second'].max() > df['logs_per_second'].min()
    
    def test_data_summary(self):
        """Test data summary generation"""
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=7)
        summary = collector.get_data_summary(df)
        
        assert 'total_points' in summary
        assert summary['total_points'] == 7 * 24
        assert 'log_volume' in summary


class TestTimeSeriesAnalyzer:
    def test_decomposition(self):
        """Test time series decomposition"""
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=30)
        
        analyzer = TimeSeriesAnalyzer()
        decomp = analyzer.decompose_time_series(df)
        
        assert 'trend' in decomp
        assert 'seasonal' in decomp
        assert 'residual' in decomp
        assert len(decomp['trend']) == len(df)
    
    def test_pattern_detection(self):
        """Test pattern strength detection"""
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=30)
        
        analyzer = TimeSeriesAnalyzer()
        patterns = analyzer.get_pattern_summary(df)
        
        assert 0 <= patterns['trend_strength'] <= 1
        assert 0 <= patterns['seasonal_strength'] <= 1
        assert 'growth_rate_monthly' in patterns


class TestForecastingEngine:
    def test_linear_forecast(self):
        """Test linear regression forecasting"""
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=30)
        df.to_csv('data/test_historical.csv', index=False)
        
        engine = ForecastingEngine()
        engine.load_historical_data('data/test_historical.csv')
        forecast = engine.forecast_linear_regression(days=7)
        
        assert 'predictions' in forecast
        assert len(forecast['predictions']) == 7 * 24
        assert all(p > 0 for p in forecast['predictions'])
    
    def test_exponential_smoothing(self):
        """Test exponential smoothing forecast"""
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=30)
        df.to_csv('data/test_historical.csv', index=False)
        
        engine = ForecastingEngine()
        engine.load_historical_data('data/test_historical.csv')
        forecast = engine.forecast_exponential_smoothing(days=7)
        
        assert 'predictions' in forecast
        assert len(forecast['predictions']) == 7 * 24


class TestResourceCalculator:
    def test_requirements_calculation(self):
        """Test resource requirements calculation"""
        calculator = ResourceCalculator()
        
        test_load = 50000  # logs per second
        requirements = calculator.calculate_requirements(test_load)
        
        assert 'nodes' in requirements
        assert requirements['nodes']['required'] > 0
        assert 'cost' in requirements
        assert requirements['cost']['monthly_usd'] > 0
    
    def test_capacity_plan(self):
        """Test capacity plan generation"""
        # Generate test forecast
        collector = MetricsCollector()
        df = collector.generate_synthetic_data(days=30)
        df.to_csv('data/test_historical.csv', index=False)
        
        engine = ForecastingEngine()
        engine.load_historical_data('data/test_historical.csv')
        forecast = engine.predict(days=7)
        
        calculator = ResourceCalculator()
        plan = calculator.generate_capacity_plan(forecast)
        
        assert 'current_capacity' in plan
        assert 'peak_requirement' in plan
        assert 'cost_projection' in plan


def test_end_to_end_workflow():
    """Test complete end-to-end workflow"""
    # 1. Collect data
    collector = MetricsCollector()
    df = collector.generate_synthetic_data(days=90)
    df.to_csv('data/test_historical.csv', index=False)
    
    # 2. Analyze patterns
    analyzer = TimeSeriesAnalyzer()
    patterns = analyzer.get_pattern_summary(df)
    assert patterns['trend_strength'] > 0
    
    # 3. Generate forecast
    engine = ForecastingEngine()
    engine.load_historical_data('data/test_historical.csv')
    forecast = engine.predict(days=30)
    assert len(forecast['predictions']) == 30 * 24
    
    # 4. Calculate requirements
    calculator = ResourceCalculator()
    plan = calculator.generate_capacity_plan(forecast)
    assert plan['peak_requirement']['nodes'] > 0
    
    print("\n✅ End-to-end workflow test passed!")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
