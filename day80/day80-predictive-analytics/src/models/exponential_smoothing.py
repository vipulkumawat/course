import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Tuple, Dict, Any
import warnings
import joblib
import os
warnings.filterwarnings('ignore')

from .base_model import BaseForecastingModel

class ExponentialSmoothingModel(BaseForecastingModel):
    """Exponential Smoothing model for time series forecasting"""
    
    def __init__(self, trend: str = 'add', seasonal: str = 'add', seasonal_periods: int = None):
        super().__init__("ExponentialSmoothing", {
            "trend": trend,
            "seasonal": seasonal, 
            "seasonal_periods": seasonal_periods
        })
        self.trend = trend
        self.seasonal = seasonal
        self.seasonal_periods = seasonal_periods or 12  # Default for hourly data
        
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit Exponential Smoothing model to time series data"""
        try:
            # Determine seasonal periods based on data frequency
            if len(y) >= 2 * self.seasonal_periods:
                seasonal = self.seasonal
                seasonal_periods = self.seasonal_periods
            else:
                seasonal = None
                seasonal_periods = None
            
            # Fit model
            self.model = ExponentialSmoothing(
                y,
                trend=self.trend,
                seasonal=seasonal,
                seasonal_periods=seasonal_periods
            )
            
            self.fitted_model = self.model.fit(optimized=True, use_boxcox=False)
            self.is_fitted = True
            self.feature_names = ['value']
            
        except Exception as e:
            print(f"Exponential Smoothing fitting failed: {e}")
            # Simple exponential smoothing fallback
            self.model = ExponentialSmoothing(y, trend=None, seasonal=None)
            self.fitted_model = self.model.fit()
            self.is_fitted = True
            
    def predict(self, steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate Exponential Smoothing predictions"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        try:
            # Generate forecast
            forecast = self.fitted_model.forecast(steps=steps)
            predictions = forecast.values if hasattr(forecast, 'values') else forecast
            
            # Simplified confidence calculation to avoid array issues
            try:
                # Calculate basic confidence based on prediction stability
                prediction_std = float(np.std(predictions))
                mean_prediction = float(np.mean(np.abs(predictions)))
                
                # Handle edge cases
                if mean_prediction == 0 or np.isnan(mean_prediction) or np.isinf(mean_prediction):
                    mean_prediction = 1.0
                
                # Calculate confidence based on coefficient of variation
                cv = prediction_std / (mean_prediction + 1e-8)
                if np.isnan(cv) or np.isinf(cv):
                    cv = 1.0
                
                # Convert to confidence (lower CV = higher confidence)
                confidence = max(0.1, min(1.0, 1.0 - cv))
                
            except Exception as e:
                print(f"Exponential Smoothing confidence calculation failed: {e}")
                confidence = 0.5
            
            # Return array of same confidence for all predictions
            return predictions, np.full(steps, confidence)
            
        except Exception as e:
            print(f"Exponential Smoothing prediction failed: {e}")
            # Fallback
            last_value = self.fitted_model.fittedvalues.iloc[-1] if hasattr(self.fitted_model, 'fittedvalues') else 0
            predictions = np.full(steps, last_value)
            confidence = np.full(steps, 0.5)
            return predictions, confidence
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'fitted_model': self.fitted_model,
            'model_name': self.model_name,
            'model_params': self.model_params,
            'is_fitted': self.is_fitted,
            'feature_names': self.feature_names,
            'last_training_time': self.last_training_time,
            'trend': self.trend,
            'seasonal': self.seasonal,
            'seasonal_periods': self.seasonal_periods
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk"""
        if os.path.exists(filepath):
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.fitted_model = model_data.get('fitted_model')
            self.model_name = model_data['model_name']
            self.model_params = model_data['model_params']
            self.is_fitted = model_data['is_fitted']
            self.feature_names = model_data['feature_names']
            self.last_training_time = model_data['last_training_time']
            self.trend = model_data.get('trend', 'add')
            self.seasonal = model_data.get('seasonal', 'add')
            self.seasonal_periods = model_data.get('seasonal_periods', 12)
