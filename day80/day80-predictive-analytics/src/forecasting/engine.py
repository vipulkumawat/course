import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import os
import sys
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models.arima_model import ARIMAModel
from src.models.prophet_model import ProphetModel
from src.models.exponential_smoothing import ExponentialSmoothingModel
from src.models.lstm_model import LSTMModel
from config.config import config

class ForecastingEngine:
    """Main forecasting engine with ensemble predictions"""
    
    def __init__(self):
        self.models = {}
        self.ensemble_weights = config.ensemble_weights
        self.load_trained_models()
        
    def load_trained_models(self):
        """Load pre-trained models"""
        model_dir = "models/trained"
        
        model_classes = {
            'arima': ARIMAModel,
            'prophet': ProphetModel,
            'exponential_smoothing': ExponentialSmoothingModel,
            # 'lstm': LSTMModel  # Temporarily disabled due to TensorFlow issues
        }
        
        for model_name, model_class in model_classes.items():
            if model_name in config.models_enabled:
                try:
                    model_path = os.path.join(model_dir, f"{model_name}_model.joblib")
                    if os.path.exists(model_path):
                        model = model_class()
                        model.load_model(model_path)
                        self.models[model_name] = model
                        print(f"✅ Loaded {model_name} model")
                    else:
                        print(f"⚠️  Model file not found: {model_path}")
                except Exception as e:
                    print(f"❌ Failed to load {model_name}: {e}")
    
    def generate_forecast(self, steps: int = None) -> Dict[str, Any]:
        """Generate ensemble forecast"""
        if steps is None:
            steps = config.forecast_horizon_minutes // 5  # 5-minute intervals
        
        forecasts = {}
        confidences = {}
        
        # Generate predictions from each model
        for model_name, model in self.models.items():
            try:
                predictions, confidence = model.predict(steps)
                forecasts[model_name] = predictions
                confidences[model_name] = confidence
            except Exception as e:
                print(f"❌ Prediction failed for {model_name}: {e}")
                forecasts[model_name] = np.zeros(steps)
                confidences[model_name] = np.zeros(steps)
        
        if not forecasts:
            return self._empty_forecast(steps)
        
        # Calculate ensemble prediction
        ensemble_prediction = np.zeros(steps)
        ensemble_confidence = np.zeros(steps)
        
        total_weight = 0
        for model_name, predictions in forecasts.items():
            weight = self.ensemble_weights.get(model_name, 0.25)
            ensemble_prediction += weight * predictions
            ensemble_confidence += weight * confidences[model_name]
            total_weight += weight
        
        if total_weight > 0:
            ensemble_prediction /= total_weight
            ensemble_confidence /= total_weight
        
        # Generate timestamps
        timestamps = [
            datetime.now() + timedelta(minutes=5 * i) 
            for i in range(1, steps + 1)
        ]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'forecast_horizon_minutes': steps * 5,
            'ensemble_prediction': ensemble_prediction.tolist(),
            'ensemble_confidence': ensemble_confidence.tolist(),
            'individual_forecasts': {
                name: preds.tolist() 
                for name, preds in forecasts.items()
            },
            'individual_confidences': {
                name: conf.tolist()
                for name, conf in confidences.items()
            },
            'timestamps': [ts.isoformat() for ts in timestamps],
            'alert_level': self._calculate_alert_level(ensemble_confidence)
        }
    
    def _calculate_alert_level(self, confidence: np.ndarray) -> str:
        """Calculate alert level based on confidence"""
        avg_confidence = np.mean(confidence)
        
        if avg_confidence >= config.high_confidence_threshold:
            return "high"
        elif avg_confidence >= config.medium_confidence_threshold:
            return "medium"
        else:
            return "low"
    
    def _empty_forecast(self, steps: int) -> Dict[str, Any]:
        """Return empty forecast when no models available"""
        return {
            'timestamp': datetime.now().isoformat(),
            'forecast_horizon_minutes': steps * 5,
            'ensemble_prediction': [0.0] * steps,
            'ensemble_confidence': [0.0] * steps,
            'individual_forecasts': {},
            'individual_confidences': {},
            'timestamps': [
                (datetime.now() + timedelta(minutes=5 * i)).isoformat()
                for i in range(1, steps + 1)
            ],
            'alert_level': "none",
            'error': "No trained models available"
        }
