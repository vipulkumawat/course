from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from forecasting.engine import ForecastingEngine
from collectors.metrics_collector import StorageMetricsCollector
from utils.cost_calculator import StorageCostCalculator
from models.storage_metrics import StorageForecast, CapacityRecommendation

app = FastAPI(title="Storage Forecasting API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
forecasting_engine = ForecastingEngine()
metrics_collector = StorageMetricsCollector()
cost_calculator = StorageCostCalculator()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/metrics/current")
async def get_current_metrics():
    """Get current storage metrics"""
    try:
        metrics = await metrics_collector.collect_current_metrics()
        return JSONResponse(content={
            "status": "success",
            "data": {
                "timestamp": metrics["timestamp"].isoformat(),
                "node_id": metrics["node_id"],
                "tenant_id": metrics["tenant_id"],
                "used_gb": metrics["used_bytes"] / (1024**3),
                "total_gb": metrics["total_bytes"] / (1024**3),
                "utilization_percent": metrics["utilization_percent"]
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/historical")
async def get_historical_metrics(days: int = 30):
    """Get historical storage metrics"""
    try:
        historical_data = metrics_collector.generate_historical_data(days)
        
        processed_data = []
        for metric in historical_data[-100:]:  # Return last 100 points
            processed_data.append({
                "timestamp": metric["timestamp"].isoformat(),
                "used_gb": metric["used_bytes"] / (1024**3),
                "utilization_percent": metric["utilization_percent"]
            })
        
        return JSONResponse(content={
            "status": "success",
            "data": processed_data,
            "total_points": len(historical_data)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast/generate")
async def generate_forecast(horizon_days: int = 30):
    """Generate storage usage forecast"""
    try:
        # Get historical data
        historical_data = metrics_collector.generate_historical_data(90)
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Generate forecast
        forecast_result = forecasting_engine.generate_ensemble_forecast(df, horizon_days)
        
        # Calculate costs
        cost_analysis = cost_calculator.calculate_forecast_costs(forecast_result)
        
        # Generate recommendations
        current_usage_gb = df['used_bytes'].iloc[-1] / (1024**3)
        future_usage_gb = forecast_result['forecast'][-1] / (1024**3)
        
        recommendation = "Monitor usage"
        if future_usage_gb > current_usage_gb * 1.5:
            recommendation = "Plan capacity expansion"
        elif future_usage_gb > current_usage_gb * 1.2:
            recommendation = "Consider optimization"
        
        response = {
            "status": "success",
            "forecast": {
                "horizon_days": horizon_days,
                "current_usage_gb": current_usage_gb,
                "predicted_usage_gb": [f / (1024**3) for f in forecast_result['forecast']],
                "confidence_lower_gb": [f / (1024**3) for f in forecast_result['lower_bound']],
                "confidence_upper_gb": [f / (1024**3) for f in forecast_result['upper_bound']],
                "dates": forecast_result['dates'],
                "model_accuracy": forecast_result['model_accuracy'],
                "best_model": forecast_result['best_model']
            },
            "cost_analysis": cost_analysis,
            "recommendation": {
                "action": recommendation,
                "risk_level": "high" if future_usage_gb > current_usage_gb * 1.5 else "medium",
                "timeline": f"Plan within {horizon_days//2} days"
            }
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

@app.get("/api/cost/scenarios")
async def get_cost_scenarios():
    """Get cost scenarios for different growth rates"""
    try:
        # Get current usage
        current_metrics = await metrics_collector.collect_current_metrics()
        current_usage_gb = current_metrics['used_bytes'] / (1024**3)
        
        # Generate scenarios
        growth_rates = [0.01, 0.02, 0.05, 0.10]  # 1%, 2%, 5%, 10% monthly growth
        scenarios = cost_calculator.generate_cost_scenarios(current_usage_gb, growth_rates)
        
        return JSONResponse(content={
            "status": "success",
            "current_usage_gb": current_usage_gb,
            "scenarios": scenarios
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for dashboard"""
    try:
        # Current metrics
        current_metrics = await metrics_collector.collect_current_metrics()
        current_usage_gb = current_metrics['used_bytes'] / (1024**3)
        
        # Generate quick 30-day forecast
        historical_data = metrics_collector.generate_historical_data(90)
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        forecast_result = forecasting_engine.generate_ensemble_forecast(df, 30)
        future_usage_gb = forecast_result['forecast'][-1] / (1024**3)
        
        # Cost calculation
        current_monthly_cost = cost_calculator.calculate_monthly_cost(current_usage_gb)
        future_monthly_cost = cost_calculator.calculate_monthly_cost(future_usage_gb)
        
        # Growth rate
        growth_rate = ((future_usage_gb - current_usage_gb) / current_usage_gb) * 100
        
        summary = {
            "current_usage_gb": round(current_usage_gb, 2),
            "predicted_usage_30d_gb": round(future_usage_gb, 2),
            "growth_rate_percent": round(growth_rate, 1),
            "current_monthly_cost": round(current_monthly_cost, 2),
            "predicted_monthly_cost": round(future_monthly_cost, 2),
            "utilization_percent": round(current_metrics['utilization_percent'], 1),
            "forecast_accuracy": round(forecast_result['model_accuracy'] * 100, 1),
            "recommendation": "Expand capacity" if growth_rate > 20 else "Monitor usage",
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(content={
            "status": "success",
            "data": summary
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
