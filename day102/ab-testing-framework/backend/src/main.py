import asyncio
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from feature_flags.api import router as feature_flags_router
from feature_flags.service import feature_flag_service
from config.settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await feature_flag_service.initialize_redis()
    yield
    # Shutdown
    if feature_flag_service.redis_client:
        await feature_flag_service.redis_client.close()

app = FastAPI(
    title="A/B Testing Framework",
    description="Feature flag and experiment management system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(feature_flags_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ab_testing_framework"}

@app.get("/")
async def root():
    return {"message": "A/B Testing Framework API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
