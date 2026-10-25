import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.api.v1.router import api_v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finregtech_shipyard")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-grade non-production backend for FinRegTech Shipyard – FCC Project Cockpit (Week 4 MVP). Implements strict role-based access control, PostgreSQL multi-schema persistence, and grounded regulatory intelligence.",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration for Harshini's Next.js/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        errors.append({
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": err.get("msg", ""),
            "type": err.get("type", "")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request payload validation failed",
            "errors": errors
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact support."},
    )

# Root landing endpoint / service index (resolves 404 on http://127.0.0.1:8000)
@app.get("/", tags=["System"], summary="API Root & Service Index")
def api_root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "version": "0.4.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "health_check": "/health",
        "api_v1_base": settings.API_V1_STR
    }

# Health check with real database and RAG microservice connectivity validation
@app.get("/health", tags=["Health"], summary="System Health Check")
def health_check():
    db_status = "connected"
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable: {str(e)}"

    rag_health = {"status": "unreachable"}
    try:
        from app.services.rag_service import get_rag_service_client
        rag_client = get_rag_service_client()
        rag_health = rag_client.check_health()
    except Exception as e:
        rag_health = {"status": "error", "error": str(e)}

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.4.0",
        "database": {
            "dialect": "postgresql",
            "status": db_status
        },
        "rag_service": rag_health
    }

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Mount OpenAPI JSON also under /api/v1/openapi.json for compatibility
@app.get("/api/v1/openapi.json", include_in_schema=False)
def api_v1_openapi():
    return app.openapi()
