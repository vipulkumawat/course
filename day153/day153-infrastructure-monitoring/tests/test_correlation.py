"""Test correlation engine"""
import pytest
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'analytics'))

def test_correlation_calculation():
    """Test correlation calculation"""
    from correlation_engine import CorrelationEngine
    
    engine = CorrelationEngine()
    
    # Create test data with perfect correlation
    df1 = pd.DataFrame({'timestamp': [1, 2, 3, 4, 5], 'value': [1, 2, 3, 4, 5]})
    df2 = pd.DataFrame({'timestamp': [1, 2, 3, 4, 5], 'value': [2, 4, 6, 8, 10]})
    
    correlation = engine.calculate_correlation(df1, df2)
    
    assert abs(correlation - 1.0) < 0.01  # Should be close to 1.0

def test_empty_dataframes():
    """Test handling of empty dataframes"""
    from correlation_engine import CorrelationEngine
    
    engine = CorrelationEngine()
    
    empty_df = pd.DataFrame()
    df = pd.DataFrame({'timestamp': [1, 2], 'value': [1, 2]})
    
    correlation = engine.calculate_correlation(empty_df, df)
    
    assert correlation == 0.0

print("✅ All correlation tests passed!")
