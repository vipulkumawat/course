import asyncio
import uvicorn
from src.api.endpoints import app
from config.delta_config import DeltaEncodingConfig

def main():
    config = DeltaEncodingConfig.from_env()
    print(f"🚀 Starting Delta Encoding Log System on port {config.dashboard_port}")
    print(f"📊 Dashboard will be available at http://localhost:{config.dashboard_port}")
    
    uvicorn.run(app, host="0.0.0.0", port=config.dashboard_port)

if __name__ == "__main__":
    main()
