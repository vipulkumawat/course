import numpy as np
import pandas as pd
import os
import joblib
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

from .base_model import BaseForecastingModel

class ARIMAModel(BaseForecastingModel):
    """ARIMA model for time series forecasting"""
    
    def __init__(self, order: Tuple[int, int, int] = (1, 1, 1)):
        super().__init__("ARIMA", {"order": order})
        self.order = order
        self.last_values = None
        
    def _check_stationarity(self, series: pd.Series) -> Tuple[bool, int]:
        """Check if series is stationary and suggest differencing"""
        result = adfuller(series.dropna())
        is_stationary = result[1] <= 0.05
        
        if not is_stationary:
            # Try differencing once
            diff_series = series.diff().dropna()
            if len(diff_series) > 10:
                diff_result = adfuller(diff_series)
                if diff_result[1] <= 0.05:
                    return False, 1
        
        return is_stationary, 0
    
    def _auto_arima_order(self, series: pd.Series) -> Tuple[int, int, int]:
        """Automatically determine ARIMA order"""
        # Check stationarity
        is_stationary, d = self._check_stationarity(series)
        
        if not is_stationary:
            d = 1
        else:
            d = 0
            
        # Simple heuristic for p and q
        # In production, use more sophisticated methods like AIC/BIC
        p = min(2, len(series) // 10)
        q = min(2, len(series) // 10)
        
        return (p, d, q)
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit ARIMA model to time series data"""
        try:
            # Use auto ARIMA if default order doesn't work well
            if self.order == (1, 1, 1) and len(y) > 50:
                self.order = self._auto_arima_order(y)
            
            # Fit ARIMA model
            self.model = ARIMA(y, order=self.order)
            self.fitted_model = self.model.fit()
            self.last_values = y.tail(max(self.order)).values
            self.is_fitted = True
            self.feature_names = ['value']
            
        except Exception as e:
            print(f"ARIMA fitting failed: {e}")
            # Fallback to simple model
            self.order = (1, 0, 0)
            self.model = ARIMA(y, order=self.order)
            self.fitted_model = self.model.fit()
            self.is_fitted = True
            
    def predict(self, steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate ARIMA predictions with confidence intervals"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        try:
            # Generate forecasts
            forecast_result = self.fitted_model.forecast(steps=steps)
            confidence_intervals = self.fitted_model.get_forecast(steps=steps).conf_int()
            
            predictions = forecast_result.values if hasattr(forecast_result, 'values') else forecast_result
            conf_lower = confidence_intervals.iloc[:, 0].values
            conf_upper = confidence_intervals.iloc[:, 1].values
            
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
                print(f"ARIMA confidence calculation failed: {e}")
                confidence = 0.5
            
            # Return array of same confidence for all predictions
            return predictions, np.full(steps, confidence)
            
        except Exception as e:
            print(f"ARIMA prediction failed: {e}")
            # Fallback prediction
            last_value = self.last_values[-1] if self.last_values is not None else 0
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
            'order': self.order,
            'last_values': self.last_values
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
            self.order = model_data.get('order', (1, 1, 1))
            self.last_values = model_data.get('last_values')
