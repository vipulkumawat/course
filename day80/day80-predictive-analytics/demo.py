#!/usr/bin/env python3
"""Demo script to showcase predictive analytics system"""

import requests
import json
import time
import sys
import os
sys.path.append('src')

from utils.data_generator import LogDataGenerator
from models.model_trainer import ModelTrainer
from forecasting.engine import ForecastingEngine

def main():
    print("🚀 Day 80: Predictive Analytics Demo")
    print("=" * 50)
    
    # Step 1: Generate sample data
    print("\n📊 Step 1: Generating sample log data...")
    generator = LogDataGenerator()
    stats = generator.save_training_data()
    print(f"   ✅ Generated {stats['web_logs']} web server logs")
    print(f"   ✅ Generated {stats['db_logs']} database logs")
    print(f"   ✅ Generated {stats['error_logs']} error logs")
    
    # Step 2: Train models
    print("\n🤖 Step 2: Training forecasting models...")
    trainer = ModelTrainer()
    results = trainer.train_all_models()
    
    for model_name, metrics in results.items():
        if 'error' not in metrics:
            print(f"   ✅ {model_name}: {metrics['accuracy']:.1%} accuracy")
        else:
            print(f"   ❌ {model_name}: Training failed")
    
    # Step 3: Generate forecasts
    print("\n🔮 Step 3: Generating predictions...")
    engine = ForecastingEngine()
    forecast = engine.generate_forecast(steps=12)  # 1-hour forecast
    
    print(f"   ✅ Generated {len(forecast['ensemble_prediction'])} predictions")
    print(f"   ✅ Average confidence: {sum(forecast['ensemble_confidence'])/len(forecast['ensemble_confidence']):.1%}")
    print(f"   ✅ Alert level: {forecast['alert_level']}")
    
    # Step 4: Display sample predictions
    print("\n📈 Step 4: Sample Predictions (Response Time)")
    print("   Time     | Prediction | Confidence")
    print("   ---------|------------|----------")
    
    for i in range(min(6, len(forecast['timestamps']))):
        timestamp = forecast['timestamps'][i][-8:-3]  # Extract HH:MM
        prediction = forecast['ensemble_prediction'][i]
        confidence = forecast['ensemble_confidence'][i]
        print(f"   {timestamp}    | {prediction:8.1f}ms | {confidence:8.1%}")
    
    # Step 5: Model comparison
    print("\n🧠 Step 5: Individual Model Predictions (first 3 steps)")
    if forecast['individual_forecasts']:
        for model_name, predictions in forecast['individual_forecasts'].items():
            if predictions:
                avg_pred = sum(predictions[:3]) / min(3, len(predictions))
                print(f"   {model_name:20}: {avg_pred:6.1f}ms average")
    
    print(f"\n✅ Demo completed successfully!")
    print(f"   📊 Dashboard: http://localhost:3000")
    print(f"   🔌 API: http://localhost:8080")
    print(f"   📈 Predictions: http://localhost:8080/predictions")

if __name__ == "__main__":
    main()
