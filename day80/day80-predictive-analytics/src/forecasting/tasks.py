from celery import Celery
import redis
import json
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecasting.engine import ForecastingEngine
from config.config import config

# Initialize Celery
app = Celery('forecasting_tasks', broker=config.redis_url)

# Redis client for storing predictions
redis_client = redis.from_url(config.redis_url)

@app.task
def generate_periodic_forecast():
    """Background task to generate forecasts periodically"""
    try:
        engine = ForecastingEngine()
        forecast = engine.generate_forecast()
        
        # Store in Redis
        redis_client.setex(
            'latest_forecast',
            ex=config.update_interval_minutes * 60,
            value=json.dumps(forecast)
        )
        
        # Store historical forecasts
        timestamp_key = f"forecast_{datetime.now().strftime('%Y%m%d_%H%M')}"
        redis_client.setex(
            timestamp_key,
            ex=24 * 3600,  # Keep for 24 hours
            value=json.dumps(forecast)
        )
        
        print(f"✅ Generated forecast at {forecast['timestamp']}")
        return forecast
        
    except Exception as e:
        print(f"❌ Forecast generation failed: {e}")
        return None

@app.task
def retrain_models():
    """Background task to retrain models periodically"""
    try:
        from models.model_trainer import ModelTrainer
        trainer = ModelTrainer()
        results = trainer.train_all_models()
        
        print(f"✅ Model retraining completed: {results}")
        return results
        
    except Exception as e:
        print(f"❌ Model retraining failed: {e}")
        return None

# Configure periodic tasks
app.conf.beat_schedule = {
    'generate-forecast': {
        'task': 'src.forecasting.tasks.generate_periodic_forecast',
        'schedule': config.update_interval_minutes * 60.0,  # Every 5 minutes
    },
    'retrain-models': {
        'task': 'src.forecasting.tasks.retrain_models', 
        'schedule': config.retrain_interval_hours * 3600.0,  # Every 6 hours
    },
}

app.conf.timezone = 'UTC'
