"""Configuration settings management for ABC Shield AI/RAG module.

Loads environment variables via pydantic-settings with safe defaults.
Resolves database and data paths deterministically relative to the package root.
"""

from pathlib import Path
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Deterministic package root independent of working directory
ROOT_DIR = Path(__file__).resolve().parent.parent


class AppSettings(BaseSettings):
    """Application-wide configuration settings."""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # Paths (deterministically resolved relative to project root)
    project_root: Path = ROOT_DIR
    data_raw_dir: Path = ROOT_DIR / "data" / "raw"
    data_processed_dir: Path = ROOT_DIR / "data" / "processed"

    # Knowledge Base / Staging vs Production
    # "canonical" points to the prepared 25-record corpus in staging (default for Fast-Track handover)
    # "legacy" points to the original 15-record corpus in data/processed
    rag_knowledge_base_mode: str = "canonical"
    rag_corpus_mode: Optional[str] = None
    canonical_chroma_persist_dir: Path = (
        ROOT_DIR / "data" / "staging" / "madhesh_handover" / "step6" / "chroma_db"
    )
    canonical_chroma_collection_name: str = "canonical_regulatory_records"
    legacy_chroma_persist_dir: Path = ROOT_DIR / "data" / "processed" / "chroma_db"
    legacy_chroma_collection_name: str = "regulatory_records"

    # Active ChromaDB configuration (defaults to canonical for Fast-Track handover)
    chroma_persist_dir: Path = (
        ROOT_DIR / "data" / "staging" / "madhesh_handover" / "step6" / "chroma_db"
    )
    chroma_collection_name: str = "canonical_regulatory_records"

    # Embedding
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # LLM Settings
    llm_provider: str = "mock"  # "mock", "openai", "ollama"
    llm_api_key: Optional[str] = None
    llm_model_name: str = "gpt-4o-mini"
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.0

    # Retrieval
    retrieval_top_k: int = 5
    min_similarity_score: float = 0.35

    # API Settings (Default port 8001 for AI/RAG microservice)
    api_host: str = "127.0.0.1"
    api_port: int = 8001
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    query_max_length: int = 2000

    @field_validator(
        "canonical_chroma_persist_dir",
        "legacy_chroma_persist_dir",
        "chroma_persist_dir",
        "data_raw_dir",
        "data_processed_dir",
        mode="after",
    )
    @classmethod
    def _resolve_paths(cls, v: Path) -> Path:
        """Resolve path relative to package root if given as a relative path."""
        if not v.is_absolute():
            return (ROOT_DIR / v).resolve()
        return v.resolve()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = AppSettings()
