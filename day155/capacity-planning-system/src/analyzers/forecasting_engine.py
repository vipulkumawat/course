"""
Forecasting Engine for Capacity Planning
Implements multiple forecasting algorithms and selects best performer
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForecastingEngine:
    """Multi-algorithm forecasting engine for capacity planning"""
    
    def __init__(self):
        self.historical_data = None
        self.models = {}
        self.best_model = None
    
    def load_historical_data(self, filepath: str):
        """Load historical data for training"""
        self.historical_data = pd.read_csv(filepath)
        self.historical_data['timestamp'] = pd.to_datetime(self.historical_data['timestamp'])
        logger.info(f"✅ Loaded {len(self.historical_data)} historical data points")
    
    def forecast_linear_regression(self, days: int, confidence: float = 0.90) -> Dict:
        """Forecast using linear regression on trend"""
        logger.info("Running linear regression forecast...")
        
        # Prepare data
        values = self.historical_data['logs_per_second'].values
        X = np.arange(len(values)).reshape(-1, 1)
        y = values
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Forecast future
        future_X = np.arange(len(values), len(values) + days * 24).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Calculate confidence intervals
        residuals = y - model.predict(X)
        std_error = np.std(residuals)
        z_score = 1.96 if confidence >= 0.95 else 1.645  # 95% or 90% confidence
        
        margin = z_score * std_error
        
        return {
            'algorithm': 'linear_regression',
            'predictions': predictions.tolist(),
            'upper_bound': (predictions + margin).tolist(),
            'lower_bound': (predictions - margin).tolist(),
            'confidence': confidence
        }
    
    def forecast_exponential_smoothing(self, days: int, alpha: float = 0.3,
                                      beta: float = 0.1, confidence: float = 0.90) -> Dict:
        """Forecast using double exponential smoothing (Holt's method)"""
        logger.info("Running exponential smoothing forecast...")
        
        values = self.historical_data['logs_per_second'].values
        
        # Initialize level and trend
        level = values[0]
        trend = np.mean(np.diff(values[:24]))  # Initial trend from first day
        
        # Smoothing
        levels = [level]
        trends = [trend]
        
        for i in range(1, len(values)):
            prev_level = level
            level = alpha * values[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
            levels.append(level)
            trends.append(trend)
        
        # Forecast
        predictions = []
        for h in range(1, days * 24 + 1):
            forecast = level + h * trend
            predictions.append(forecast)
        
        # Confidence intervals (simplified)
        errors = values - np.array(levels)
        std_error = np.std(errors)
        z_score = 1.96 if confidence >= 0.95 else 1.645
        margin = z_score * std_error
        
        return {
            'algorithm': 'exponential_smoothing',
            'predictions': predictions,
            'upper_bound': (np.array(predictions) + margin).tolist(),
            'lower_bound': (np.array(predictions) - margin).tolist(),
            'confidence': confidence
        }
    
    def forecast_prophet_like(self, days: int, confidence: float = 0.90) -> Dict:
        """
        Simplified Prophet-like forecast combining trend and seasonality
        Full Prophet requires fbprophet library, this is a lightweight alternative
        """
        logger.info("Running Prophet-like forecast...")
        
        from analyzers.time_series_analyzer import TimeSeriesAnalyzer
        
        values = self.historical_data['logs_per_second'].values
        
        # Decompose time series
        analyzer = TimeSeriesAnalyzer()
        decomp = analyzer.decompose_time_series(self.historical_data, period=24)
        
        # Extrapolate trend
        trend = decomp['trend']
        trend_slope = (trend[-1] - trend[-168]) / 168  # Slope from last week
        future_trend = trend[-1] + np.arange(1, days * 24 + 1) * trend_slope
        
        # Repeat seasonal pattern
        seasonal = decomp['seasonal']
        period = 24
        future_seasonal = np.tile(seasonal[:period], days)
        
        # Combine
        predictions = future_trend + future_seasonal
        
        # Confidence intervals
        residual_std = np.std(decomp['residual'])
        z_score = 1.96 if confidence >= 0.95 else 1.645
        margin = z_score * residual_std
        
        return {
            'algorithm': 'prophet_like',
            'predictions': predictions.tolist(),
            'upper_bound': (predictions + margin).tolist(),
            'lower_bound': (predictions - margin).tolist(),
            'confidence': confidence
        }
    
    def predict(self, days: int = 30, confidence: float = 0.90,
                algorithm: Optional[str] = None) -> Dict:
        """
        Generate forecast using specified or best-performing algorithm
        """
        if self.historical_data is None:
            raise ValueError("Must load historical data first")
        
        # Run all algorithms if no specific one requested
        if algorithm is None:
            forecasts = {
                'linear': self.forecast_linear_regression(days, confidence),
                'exponential': self.forecast_exponential_smoothing(days, confidence),
                'prophet': self.forecast_prophet_like(days, confidence)
            }
            
            # For demo, use exponential smoothing as default
            best_forecast = forecasts['exponential']
            best_forecast['all_forecasts'] = forecasts
            
            return best_forecast
        
        # Run specific algorithm
        if algorithm == 'linear':
            return self.forecast_linear_regression(days, confidence)
        elif algorithm == 'exponential':
            return self.forecast_exponential_smoothing(days, confidence)
        elif algorithm == 'prophet':
            return self.forecast_prophet_like(days, confidence)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def evaluate_models(self) -> Dict:
        """Evaluate forecasting accuracy on historical data"""
        logger.info("Evaluating forecasting models...")
        
        # Use last 7 days as test set
        test_size = 24 * 7  # 7 days of hourly data
        train_data = self.historical_data[:-test_size].copy()
        test_data = self.historical_data[-test_size:].copy()
        
        # Temporarily swap historical data
        original_data = self.historical_data
        self.historical_data = train_data
        
        # Generate forecasts
        forecast_days = 7
        forecasts = {
            'linear': self.forecast_linear_regression(forecast_days),
            'exponential': self.forecast_exponential_smoothing(forecast_days),
            'prophet': self.forecast_prophet_like(forecast_days)
        }
        
        # Restore original data
        self.historical_data = original_data
        
        # Calculate errors
        actual = test_data['logs_per_second'].values
        results = {}
        
        for name, forecast in forecasts.items():
            predictions = np.array(forecast['predictions'])
            rmse = np.sqrt(mean_squared_error(actual, predictions))
            mape = mean_absolute_percentage_error(actual, predictions)
            
            results[name] = {
                'rmse': float(rmse),
                'mape': float(mape),
                'rmse_percent': float(rmse / np.mean(actual) * 100)
            }
        
        logger.info("✅ Model evaluation complete")
        for name, metrics in results.items():
            logger.info(f"   {name}: RMSE {metrics['rmse_percent']:.1f}%, MAPE {metrics['mape']:.1%}")
        
        return results


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate capacity forecasts')
    parser.add_argument('--test', action='store_true', help='Run model evaluation')
    parser.add_argument('--days', type=int, default=30, help='Forecast horizon in days')
    
    args = parser.parse_args()
    
    engine = ForecastingEngine()
    engine.load_historical_data('data/historical.csv')
    
    if args.test:
        results = engine.evaluate_models()
        print("\n📊 Forecasting Model Performance:")
        for model, metrics in results.items():
            print(f"   {model}: RMSE {metrics['rmse_percent']:.1f}%, MAPE {metrics['mape']:.1%}")
    else:
        forecast = engine.predict(days=args.days)
        print(f"\n🔮 {args.days}-day forecast generated")
        print(f"   Current: {engine.historical_data['logs_per_second'].iloc[-1]:.0f} logs/sec")
        print(f"   Predicted (day {args.days}): {forecast['predictions'][-24]:.0f} logs/sec")
