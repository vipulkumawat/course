import asyncio
import uvicorn
from src.api.forecast_api import app

def main():
    print("🚀 Starting Storage Forecasting System")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
    
    uvicorn.run(
        "src.api.forecast_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
