"""Health check response models for API monitoring."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """High-level system health and status payload."""

    status: str = Field("ok", description="Overall API service health status")
    app_name: str = Field("ABC Shield FinRegTech API", description="Application service name")
    version: str = Field("1.0.0", description="API service version")
    rag_pipeline_initialized: bool = Field(True, description="Whether RAG pipeline components are initialized")
    chromadb_status: str = Field("connected", description="ChromaDB persistent vector store connectivity status")
    environment: str = Field("development", description="Operational environment tier")
