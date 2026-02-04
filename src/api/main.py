"""
CloudCost Optimizer - Main FastAPI Application
AWS Instance Price Optimizer & Recommender
"""

from contextlib import asynccontextmanager
from datetime import datetime
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from src.core.config import settings
from src.core.database import init_db, close_db
from src.core.cache import init_redis, close_redis
from src.api.middleware.rate_limiter import RateLimiterMiddleware
from src.api.routes import (
    health_router,
    instances_router,
    pricing_router,
    recommendations_router,
)
from src.api.routes.multicloud import router as multicloud_router
from src.api.routes.ai import router as ai_router
from src.api.routes.spot_intelligence import router as spot_intelligence_router
from src.api.routes.debug import router as debug_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize Redis
        await init_redis()
        logger.info("Redis cache initialized")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_redis()
    await close_db()
    logger.info("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## AWS Instance Price Optimizer & Recommender

CloudCost Optimizer helps you find the most cost-effective AWS EC2 instances
for your workloads. It analyzes pricing across On-Demand, Reserved, and Spot
instances to provide intelligent recommendations.

### Features

- **Multi-Cloud Support**: Compare AWS, GCP, and Azure instances
- **Instance Discovery**: Browse and filter 600+ instance types across clouds
- **Price Comparison**: Compare pricing across regions and strategies
- **Smart Recommendations**: Get AI-powered instance recommendations
- **Cross-Cloud Analysis**: Find equivalent instances across providers
- **Spot Analysis**: Track spot prices and interruption risks

### Pricing Strategies

- **On-Demand**: Pay by the hour, maximum flexibility
- **Reserved**: 1-3 year commitments, up to 60% savings
- **Spot**: Unused capacity, up to 90% savings

### Getting Started

1. Use `/instances` to explore available instance types
2. Use `/pricing` to get current prices
3. Use `/recommendations` to get personalized suggestions
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression middleware (compress responses > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting middleware
app.add_middleware(RateLimiterMiddleware)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Include routers
app.include_router(health_router)
app.include_router(instances_router, prefix="/api/v1")
app.include_router(pricing_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(multicloud_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")  # CloudCost AI™
app.include_router(spot_intelligence_router, prefix="/api/v1")  # Spot Intelligence™ - FIX: Changed from /api/v1/spot-intelligence
app.include_router(debug_router, prefix="/api/v1")  # Debug endpoints (temporary)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "description": "AWS Instance Price Optimizer & Recommender",
        "documentation": "/docs",
        "health": "/health",
        "endpoints": {
            "instances": "/api/v1/instances",
            "pricing": "/api/v1/pricing",
            "recommendations": "/api/v1/recommendations",
            "multicloud": "/api/v1/multicloud",
        },
    }


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.app_name,
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring",
        },
        {
            "name": "Instances",
            "description": "AWS EC2 instance type information and specifications",
        },
        {
            "name": "Pricing",
            "description": "Pricing data for On-Demand, Reserved, and Spot instances",
        },
        {
            "name": "Recommendations",
            "description": "Intelligent instance recommendations based on workload requirements",
        },
        {
            "name": "Multi-Cloud",
            "description": "Cross-cloud comparison and recommendations for AWS, GCP, and Azure",
        },
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

