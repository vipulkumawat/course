from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List
import joblib
import os

class BaseForecastingModel(ABC):
    """Base class for all forecasting models"""
    
    def __init__(self, model_name: str, model_params: Dict[str, Any] = None):
        self.model_name = model_name
        self.model_params = model_params or {}
        self.model = None
        self.is_fitted = False
        self.feature_names = None
        self.last_training_time = None
        
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model on historical data"""
        pass
    
    @abstractmethod
    def predict(self, steps: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate predictions with confidence intervals"""
        pass
    
    def validate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Validate model performance"""
        if not self.is_fitted:
            raise ValueError(f"Model {self.model_name} must be fitted before validation")
            
        predictions, _ = self.predict(len(y_test))
        
        # Calculate metrics
        mae = np.mean(np.abs(predictions - y_test.values))
        mse = np.mean((predictions - y_test.values) ** 2)
        rmse = np.sqrt(mse)
        
        # Calculate accuracy based on relative error
        relative_errors = np.abs(predictions - y_test.values) / (y_test.values + 1e-8)
        accuracy = 1 - np.mean(relative_errors)
        
        return {
            'mae': mae,
            'mse': mse, 
            'rmse': rmse,
            'accuracy': max(0, accuracy)  # Ensure non-negative accuracy
        }
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'model_name': self.model_name,
            'model_params': self.model_params,
            'is_fitted': self.is_fitted,
            'feature_names': self.feature_names,
            'last_training_time': self.last_training_time
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk"""
        if os.path.exists(filepath):
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.model_name = model_data['model_name']
            self.model_params = model_data['model_params']
            self.is_fitted = model_data['is_fitted']
            self.feature_names = model_data['feature_names']
            self.last_training_time = model_data['last_training_time']
