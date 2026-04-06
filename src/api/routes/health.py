"""
Health Check Endpoints
Provides health and readiness checks for the API.
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.cache import redis_client
from src.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check() -> Dict:
    """
    Basic health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict:
    """
    Readiness check - verifies database and cache connectivity.
    
    Returns:
        Detailed readiness status
    """
    checks = {
        "database": False,
        "cache": False,
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)
    
    # Redis is optional (e.g. Render deploys without Redis)
    redis_configured = bool(settings.redis_url)
    try:
        if not redis_configured:
            checks["cache"] = "disabled"
        elif redis_client:
            await redis_client.ping()
            checks["cache"] = True
        else:
            checks["cache"] = False
            checks["cache_error"] = "not connected"
    except Exception as e:
        checks["cache_error"] = str(e)

    cache_ok = (not redis_configured) or (checks.get("cache") is True)
    all_healthy = checks["database"] and cache_ok
    
    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/live")
async def liveness_check() -> Dict:
    """
    Liveness check - simple alive indicator.
    
    Returns:
        Alive status
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }

