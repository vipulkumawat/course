#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import redis
import json
from datetime import datetime, timedelta
import sys
import os
# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.forecasting.engine import ForecastingEngine
from config.config import config

app = FastAPI(title="Predictive Analytics API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis client
redis_client = redis.from_url(config.redis_url)

# Initialize forecasting engine
forecasting_engine = ForecastingEngine()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Predictive Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "predictions": "/predictions",
            "forecast": "/forecast/{steps}",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Redis connection
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    # Check model availability
    models_loaded = len(forecasting_engine.models)
    
    return {
        "status": "healthy" if redis_status == "connected" and models_loaded > 0 else "degraded",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": redis_status,
            "models_loaded": models_loaded,
            "models_available": list(forecasting_engine.models.keys())
        }
    }

@app.get("/predictions")
async def get_latest_predictions():
    """Get latest cached predictions"""
    try:
        forecast_data = redis_client.get('latest_forecast')
        if forecast_data:
            return json.loads(forecast_data)
        else:
            # Generate fresh forecast if none cached
            forecast = forecasting_engine.generate_forecast()
            redis_client.setex(
                'latest_forecast',
                config.update_interval_minutes * 60,
                json.dumps(forecast)
            )
            return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get predictions: {str(e)}")

@app.get("/forecast/{steps}")
async def generate_forecast(steps: int):
    """Generate forecast for specified number of steps"""
    if steps <= 0 or steps > 288:  # Max 24 hours (288 * 5 minutes)
        raise HTTPException(status_code=400, detail="Steps must be between 1 and 288")
    
    try:
        forecast = forecasting_engine.generate_forecast(steps)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")

@app.get("/metrics")
async def get_metrics():
    """Get system metrics and model performance"""
    try:
        # Get latest forecast
        forecast_data = redis_client.get('latest_forecast')
        latest_forecast = json.loads(forecast_data) if forecast_data else None
        
        # Calculate metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "models_active": len(forecasting_engine.models),
            "last_forecast_time": latest_forecast['timestamp'] if latest_forecast else None,
            "forecast_confidence": {
                "high": 0,
                "medium": 0, 
                "low": 0
            }
        }
        
        if latest_forecast:
            confidence_levels = latest_forecast.get('ensemble_confidence', [])
            if confidence_levels:
                high_conf = sum(1 for c in confidence_levels if c >= config.high_confidence_threshold)
                medium_conf = sum(1 for c in confidence_levels if config.medium_confidence_threshold <= c < config.high_confidence_threshold)
                low_conf = len(confidence_levels) - high_conf - medium_conf
                
                metrics["forecast_confidence"] = {
                    "high": high_conf,
                    "medium": medium_conf,
                    "low": low_conf
                }
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@app.get("/historical/{hours}")
async def get_historical_forecasts(hours: int = 24):
    """Get historical forecasts for analysis"""
    if hours <= 0 or hours > 168:  # Max 1 week
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
    
    try:
        historical_data = []
        now = datetime.now()
        
        # Get forecasts from the last N hours
        for i in range(0, hours * 12):  # 12 forecasts per hour (every 5 minutes)
            timestamp = now - timedelta(minutes=5 * i)
            key = f"forecast_{timestamp.strftime('%Y%m%d_%H%M')}"
            data = redis_client.get(key)
            
            if data:
                historical_data.append(json.loads(data))
        
        return {
            "historical_forecasts": historical_data,
            "count": len(historical_data),
            "period_hours": hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get historical data: {str(e)}")

@app.post("/demo/run")
async def run_demo():
    """Run demo to generate sample data and train models"""
    try:
        # Import the modules directly instead of using subprocess
        import importlib.util
        
        # Step 1: Generate sample data
        print("📊 Generating sample log data...")
        from src.utils.data_generator import LogDataGenerator
        generator = LogDataGenerator()
        generator.save_training_data()
        
        # Step 2: Train models
        print("🤖 Training forecasting models...")
        from src.models.model_trainer import ModelTrainer
        trainer = ModelTrainer()
        trainer.train_all_models()
        
        # Step 3: Reload models in forecasting engine
        print("🔄 Reloading models...")
        forecasting_engine.load_trained_models()
        
        # Step 4: Generate fresh forecast
        print("🔮 Generating ensemble predictions...")
        forecast = forecasting_engine.generate_forecast()
        
        # Cache the forecast
        redis_client.setex(
            'latest_forecast',
            config.update_interval_minutes * 60,
            json.dumps(forecast)
        )
        
        return {
            "status": "success",
            "message": "Demo completed successfully",
            "models_loaded": len(forecasting_engine.models),
            "forecast_generated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)
