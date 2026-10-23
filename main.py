"""FastAPI application entrypoint for ABC Shield FinRegTech prototype.

Exposes the unified Task 9 StructuredAIResponse contract to backend (Vishal) and
frontend (Harshini) consumers with configurable CORS, health monitoring, and safe error handling.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from api.routes.health import router as health_router
from api.routes.query import router as query_router
from api.routes.compare import router as compare_router
from config.settings import settings

logger = logging.getLogger(__name__)

# Initialize FastAPI application with comprehensive metadata
app = FastAPI(
    title="ABC Shield FinRegTech API",
    description=(
        "Source-grounded regulatory intelligence and compliance engine for ABC Shield / FinRegTech ShipYard. "
        "Unifies semantic vector retrieval, grounded LLM generation, deterministic citations, evidence GAP handling, "
        "and conflict detection into a single stable REST API contract.\n\n"
        "**Legal Notice**: This system is a development prototype and provides source-grounded regulatory intelligence. "
        "It does not constitute formal legal advice. All current regulatory records are marked Candidate - Awaiting Approval."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS Middleware
# Uses configured origins to allow frontend development without hardcoded wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health_router)
app.include_router(query_router)
app.include_router(compare_router)



# Global unhandled exception handler ensuring no internal stack traces or secrets leak to clients
@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler preventing stack traces or filesystem paths from leaking."""
    logger.exception("Unhandled server exception processing path '%s': %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred. Please contact the administrator."
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
