"""Route modules for FastAPI application."""

from api.routes.health import router as health_router
from api.routes.query import router as query_router
from api.routes.compare import router as compare_router

__all__ = ["health_router", "query_router", "compare_router"]

