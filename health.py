"""Health and monitoring endpoints for ABC Shield API."""

from fastapi import APIRouter
from api.models.health import HealthResponse
from api.dependencies import check_chromadb_connectivity
from config.settings import settings

router = APIRouter(tags=["Health & Status"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Root service health check",
    description="Returns high-level service status, RAG pipeline readiness, and vector store connectivity without leaking internal paths.",
)
@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Versioned service health check",
    description="Returns high-level service status, RAG pipeline readiness, and vector store connectivity for API v1 consumers.",
)
def get_health() -> HealthResponse:
    """Retrieve operational status for load balancers and system monitoring."""
    chroma_ok = check_chromadb_connectivity()
    return HealthResponse(
        status="ok" if chroma_ok else "degraded",
        app_name="ABC Shield FinRegTech API",
        version="1.0.0",
        rag_pipeline_initialized=True,
        chromadb_status="connected" if chroma_ok else "disconnected",
        environment=settings.environment,
    )
