import os
from pydantic import BaseModel
from typing import Dict, List, Any

class PredictiveConfig(BaseModel):
    # Data sources
    redis_url: str = "redis://localhost:6379/0"
    data_retention_days: int = 30
    
    # Forecasting parameters
    forecast_horizon_minutes: int = 60
    update_interval_minutes: int = 5
    confidence_threshold: float = 0.8
    
    # Model configuration
    models_enabled: List[str] = ["arima", "prophet", "exponential_smoothing"]
    ensemble_weights: Dict[str, float] = {
        "arima": 0.35,
        "prophet": 0.45, 
        "exponential_smoothing": 0.20
    }
    
    # Alert thresholds
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.65
    
    # API configuration
    api_host: str = "localhost"
    api_port: int = 8080
    enable_cors: bool = True
    
    # Training configuration
    min_training_samples: int = 100
    retrain_interval_hours: int = 6
    validation_split: float = 0.2

config = PredictiveConfig()
