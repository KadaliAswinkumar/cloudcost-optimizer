from src.api.routes.instances import router as instances_router
from src.api.routes.pricing import router as pricing_router
from src.api.routes.recommendations import router as recommendations_router
from src.api.routes.health import router as health_router

__all__ = [
    "instances_router",
    "pricing_router", 
    "recommendations_router",
    "health_router",
]

