from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any
import json
import asyncio
import logging
from src.pipeline.log_processor import LogProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Field-Level Encryption Dashboard", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize log processor
log_processor = LogProcessor()

class TestDataModel(BaseModel):
    data: Dict[str, Any]

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    """Get current system statistics."""
    try:
        stats = log_processor.get_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logging.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test-encryption")
async def test_encryption(test_data: TestDataModel):
    """Test encryption with sample data."""
    try:
        logging.info(f"Received encryption test data: {test_data.data}")
        
        if not test_data.data:
            raise HTTPException(status_code=422, detail="No data provided")
        
        result = await log_processor.process_log(test_data.data)
        logging.info(f"Encryption completed successfully")
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Encryption test failed: {e}")
        if "422" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/test-decryption")
async def test_decryption(test_data: TestDataModel):
    """Test decryption with encrypted data."""
    try:
        logging.info(f"Received decryption test data")
        result = log_processor.decrypt_log(test_data.data)
        logging.info(f"Decryption completed successfully")
        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Decryption test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "field-encryption-dashboard"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
