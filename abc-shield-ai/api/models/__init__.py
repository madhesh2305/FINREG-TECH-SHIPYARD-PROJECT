"""Pydantic models for FastAPI request and health contracts."""

from api.models.query import QueryRequest
from api.models.health import HealthResponse

__all__ = ["QueryRequest", "HealthResponse"]
