#!/usr/bin/env python3
"""Model training and management system"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
from src.utils.data_loader import DataLoader
from config.config import config

class ModelTrainer:
    """Train and evaluate forecasting models"""
    
    def __init__(self):
        self.models = {
            'arima': ARIMAModel(),
            'prophet': ProphetModel(),
            'exponential_smoothing': ExponentialSmoothingModel(),
            'lstm': LSTMModel(sequence_length=30, epochs=20)
        }
        self.data_loader = DataLoader()
        self.model_dir = "models/trained"
        os.makedirs(self.model_dir, exist_ok=True)
        
    def train_all_models(self):
        """Train all enabled models"""
        print("🤖 Starting model training...")
        
        # Load training data
        data = self.data_loader.load_training_data()
        if data is None or len(data) < config.min_training_samples:
            print(f"❌ Insufficient training data. Need at least {config.min_training_samples} samples")
            return
        
        # Prepare data
        X = data[['timestamp']].copy()
        X.set_index('timestamp', inplace=True)
        y = data['response_time']
        
        print(f"📊 Training on {len(data)} samples...")
        
        # Train each model
        results = {}
        for model_name, model in self.models.items():
            if model_name in config.models_enabled:
                print(f"🔧 Training {model_name}...")
                try:
                    # Split data for validation
                    split_idx = int(len(data) * (1 - config.validation_split))
                    X_train, X_val = X[:split_idx], X[split_idx:]
                    y_train, y_val = y[:split_idx], y[split_idx:]
                    
                    # Train model
                    model.fit(X_train, y_train)
                    
                    # Validate
                    if len(y_val) > 0:
                        validation_metrics = model.validate(X_val, y_val)
                        results[model_name] = validation_metrics
                        print(f"✅ {model_name}: Accuracy = {validation_metrics['accuracy']:.3f}")
                    
                    # Save trained model
                    model_path = os.path.join(self.model_dir, f"{model_name}_model.joblib")
                    model.save_model(model_path)
                    
                except Exception as e:
                    print(f"❌ Failed to train {model_name}: {e}")
                    results[model_name] = {'accuracy': 0.0, 'error': str(e)}
        
        # Save training results
        with open(os.path.join(self.model_dir, 'training_results.json'), 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results,
                'training_samples': len(data)
            }, f, indent=2)
        
        print(f"🎯 Model training completed. Results saved to {self.model_dir}")
        return results

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all_models()
