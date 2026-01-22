"""
Time-Series Analyzer for Capacity Planning
Decomposes time series into trend, seasonality, and residual components
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesAnalyzer:
    """Analyzes time series data to identify patterns and trends"""
    
    def __init__(self):
        self.decomposition = None
    
    def decompose_time_series(self, df: pd.DataFrame, 
                              value_column: str = 'logs_per_second',
                              period: int = 24) -> Dict:
        """
        Decompose time series into trend, seasonal, and residual components
        Uses additive decomposition: y = trend + seasonal + residual
        """
        logger.info("Decomposing time series into components...")
        
        values = df[value_column].values
        n = len(values)
        
        # 1. Calculate trend using moving average
        trend = self._calculate_trend(values, window=period)
        
        # 2. Detrend the data
        detrended = values - trend
        
        # 3. Calculate seasonal component
        seasonal = self._calculate_seasonality(detrended, period=period)
        
        # 4. Calculate residual
        residual = values - trend - seasonal
        
        self.decomposition = {
            'original': values,
            'trend': trend,
            'seasonal': seasonal,
            'residual': residual,
            'period': period
        }
        
        logger.info("✅ Time series decomposition complete")
        self._log_decomposition_stats()
        
        return self.decomposition
    
    def _calculate_trend(self, values: np.ndarray, window: int) -> np.ndarray:
        """Calculate trend using centered moving average"""
        trend = np.zeros_like(values, dtype=float)
        half_window = window // 2
        
        for i in range(len(values)):
            start = max(0, i - half_window)
            end = min(len(values), i + half_window + 1)
            trend[i] = np.mean(values[start:end])
        
        return trend
    
    def _calculate_seasonality(self, detrended: np.ndarray, period: int) -> np.ndarray:
        """Calculate seasonal component by averaging same periods"""
        n = len(detrended)
        seasonal_avg = np.zeros(period)
        
        # Average all occurrences of each period
        for i in range(period):
            indices = np.arange(i, n, period)
            seasonal_avg[i] = np.mean(detrended[indices])
        
        # Normalize to zero mean
        seasonal_avg -= np.mean(seasonal_avg)
        
        # Repeat pattern for full length
        seasonal = np.tile(seasonal_avg, n // period + 1)[:n]
        
        return seasonal
    
    def detect_trend_strength(self) -> float:
        """Calculate strength of trend component (0-1)"""
        if self.decomposition is None:
            raise ValueError("Must run decompose_time_series first")
        
        residual_var = np.var(self.decomposition['residual'])
        detrended_var = np.var(self.decomposition['original'] - self.decomposition['trend'])
        
        # Trend strength: 1 - (residual_var / detrended_var)
        trend_strength = max(0, 1 - (residual_var / detrended_var))
        
        return float(trend_strength)
    
    def detect_seasonality_strength(self) -> float:
        """Calculate strength of seasonal component (0-1)"""
        if self.decomposition is None:
            raise ValueError("Must run decompose_time_series first")
        
        residual_var = np.var(self.decomposition['residual'])
        deseasonal_var = np.var(self.decomposition['original'] - self.decomposition['seasonal'])
        
        # Seasonality strength: 1 - (residual_var / deseasonal_var)
        seasonal_strength = max(0, 1 - (residual_var / deseasonal_var))
        
        return float(seasonal_strength)
    
    def calculate_growth_rate(self, df: pd.DataFrame, 
                             value_column: str = 'logs_per_second',
                             window_days: int = 30) -> float:
        """Calculate recent growth rate (percentage per month)"""
        values = df[value_column].values
        window_hours = window_days * 24
        
        if len(values) < window_hours:
            window_hours = len(values) // 2
        
        recent = values[-window_hours:]
        start_avg = np.mean(recent[:window_hours//3])
        end_avg = np.mean(recent[-window_hours//3:])
        
        if start_avg == 0:
            return 0.0
        
        growth_rate = ((end_avg / start_avg) - 1) * (30 / window_days)
        
        return float(growth_rate)
    
    def _log_decomposition_stats(self):
        """Log statistics about decomposition"""
        trend_strength = self.detect_trend_strength()
        seasonal_strength = self.detect_seasonality_strength()
        
        logger.info(f"   Trend strength: {trend_strength:.2%}")
        logger.info(f"   Seasonal strength: {seasonal_strength:.2%}")
    
    def get_pattern_summary(self, df: pd.DataFrame) -> Dict:
        """Generate summary of detected patterns"""
        self.decompose_time_series(df)
        growth_rate = self.calculate_growth_rate(df)
        
        return {
            'trend_strength': self.detect_trend_strength(),
            'seasonal_strength': self.detect_seasonality_strength(),
            'growth_rate_monthly': growth_rate,
            'has_strong_trend': self.detect_trend_strength() > 0.6,
            'has_strong_seasonality': self.detect_seasonality_strength() > 0.6
        }


if __name__ == '__main__':
    from collectors.metrics_collector import MetricsCollector
    
    # Test analyzer
    collector = MetricsCollector()
    df = collector.generate_synthetic_data(90)
    
    analyzer = TimeSeriesAnalyzer()
    patterns = analyzer.get_pattern_summary(df)
    
    print("\n📊 Pattern Analysis Results:")
    print(f"   Trend Strength: {patterns['trend_strength']:.2%}")
    print(f"   Seasonal Strength: {patterns['seasonal_strength']:.2%}")
    print(f"   Growth Rate: {patterns['growth_rate_monthly']:.2%} per month")
    print(f"   Strong Trend: {'Yes' if patterns['has_strong_trend'] else 'No'}")
    print(f"   Strong Seasonality: {'Yes' if patterns['has_strong_seasonality'] else 'No'}")
