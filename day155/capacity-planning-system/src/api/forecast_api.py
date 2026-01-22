"""
FastAPI application for capacity planning forecasts
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import yaml
import logging

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from collectors.metrics_collector import MetricsCollector
from analyzers.time_series_analyzer import TimeSeriesAnalyzer
from analyzers.forecasting_engine import ForecastingEngine
from calculators.resource_calculator import ResourceCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Capacity Planning API",
    description="Resource forecasting based on log volume trends",
    version="1.0.0"
)

# Load configuration
with open('config/planning_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['api']['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
collector = MetricsCollector()
analyzer = TimeSeriesAnalyzer()
forecaster = ForecastingEngine()
calculator = ResourceCalculator()


class ForecastRequest(BaseModel):
    days: int = 30
    confidence: float = 0.90
    algorithm: Optional[str] = None


class CapacityRecommendation(BaseModel):
    current_nodes: int
    required_nodes: int
    nodes_to_add: int
    estimated_cost_monthly: float


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("🚀 Starting Capacity Planning API...")
    
    # Collect initial data
    df = collector.collect_historical_data(days=90)
    collector.save_historical_data(df)
    forecaster.load_historical_data('data/historical.csv')
    
    logger.info("✅ API ready to serve forecasts")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Capacity Planning API",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/api/forecast/{days}days")
async def generate_forecast(days: int, confidence: float = 0.90):
    """Generate capacity forecast for specified days"""
    try:
        if days < 1 or days > 90:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 90")
        
        forecast = forecaster.predict(days=days, confidence=confidence)
        
        # Get current and predicted values
        current_load = forecaster.historical_data['logs_per_second'].iloc[-1]
        predicted_load = forecast['predictions'][-24]  # Last day average
        
        return {
            "forecast_days": days,
            "confidence_level": confidence,
            "current_logs_per_second": float(current_load),
            "predicted_logs_per_second": float(predicted_load),
            "growth_percentage": float((predicted_load / current_load - 1) * 100),
            "predictions": forecast['predictions'],
            "upper_bound": forecast['upper_bound'],
            "lower_bound": forecast['lower_bound']
        }
    
    except Exception as e:
        logger.error(f"Forecast generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capacity/current")
async def get_current_capacity():
    """Get current cluster capacity and utilization"""
    try:
        current_load = forecaster.historical_data['logs_per_second'].iloc[-1]
        requirements = calculator.calculate_requirements(current_load)
        
        return {
            "current_load_logs_per_second": float(current_load),
            "nodes": requirements['nodes'],
            "resources": requirements['resources'],
            "utilization": requirements['nodes']['capacity_utilization']
        }
    
    except Exception as e:
        logger.error(f"Current capacity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capacity/recommendations")
async def get_capacity_recommendations():
    """Get capacity planning recommendations"""
    try:
        # Generate 30-day forecast
        forecast = forecaster.predict(days=30)
        
        # Generate capacity plan
        plan = calculator.generate_capacity_plan(forecast)
        
        return {
            "forecast_period": "30 days",
            "current_capacity": plan['current_capacity'],
            "peak_requirement": plan['peak_requirement'],
            "scale_events": plan['scale_events'],
            "cost_projection": plan['cost_projection'],
            "recommendation": f"Add {plan['peak_requirement']['nodes'] - plan['current_capacity']['nodes']} nodes by day {plan['peak_requirement']['day']}"
        }
    
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/patterns")
async def get_pattern_analysis():
    """Get time-series pattern analysis"""
    try:
        patterns = analyzer.get_pattern_summary(forecaster.historical_data)
        
        return {
            "trend_strength": patterns['trend_strength'],
            "seasonal_strength": patterns['seasonal_strength'],
            "growth_rate_monthly": patterns['growth_rate_monthly'],
            "has_strong_trend": patterns['has_strong_trend'],
            "has_strong_seasonality": patterns['has_strong_seasonality']
        }
    
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """Get summary of collected metrics"""
    try:
        summary = collector.get_data_summary(forecaster.historical_data)
        return summary
    
    except Exception as e:
        logger.error(f"Metrics summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
