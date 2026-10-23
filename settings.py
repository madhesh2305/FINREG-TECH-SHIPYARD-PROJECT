"""Configuration settings management for ABC Shield AI/RAG module.

Loads environment variables via pydantic-settings with safe defaults.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application-wide configuration settings."""

    # Environment
    environment: str = "development"
    log_level: str = "INFO"

    # Paths
    data_raw_dir: Path = Path("data/raw")
    data_processed_dir: Path = Path("data/processed")

    # Knowledge Base / Staging vs Production
    # "canonical" points to the prepared 25-record corpus in staging (default for Fast-Track handover)
    # "legacy" points to the original 15-record corpus in data/processed
    rag_knowledge_base_mode: str = "canonical"
    canonical_chroma_persist_dir: Path = Path("data/staging/madhesh_handover/step6/chroma_db")
    canonical_chroma_collection_name: str = "canonical_regulatory_records"
    legacy_chroma_persist_dir: Path = Path("data/processed/chroma_db")
    legacy_chroma_collection_name: str = "regulatory_records"

    # Active ChromaDB configuration (defaults to canonical for Fast-Track handover)
    chroma_persist_dir: Path = Path("data/staging/madhesh_handover/step6/chroma_db")
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

    # API Settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    query_max_length: int = 2000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = AppSettings()
