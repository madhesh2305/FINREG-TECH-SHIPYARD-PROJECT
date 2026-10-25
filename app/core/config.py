import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_backend_env = os.path.join(_backend_dir, ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "FinRegTech Shipyard - FCC Project Cockpit"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    SQLITE_FALLBACK_URL: str = "sqlite:///./finregtech_dev.db"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    # AI/RAG Microservice Integration
    RAG_SERVICE_URL: str = "http://127.0.0.1:8001"
    RAG_SERVICE_TIMEOUT_SECONDS: float = 35.0

    model_config = SettingsConfigDict(
        env_file=[_backend_env, ".env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("DATABASE_URL must be provided via environment or .env file.")
        return v.strip()

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or len(v.strip()) < 32:
            raise ValueError("SECRET_KEY must be configured with at least 32 cryptographically secure characters.")
        insecure_fallbacks = [
            "finregtech-shipyard-secret-key-change-in-production-min-32-bytes",
            "secret",
            "changeme",
        ]
        if v.strip() in insecure_fallbacks:
            raise ValueError("Insecure default SECRET_KEY detected. A cryptographically secure secret must be configured.")
        return v.strip()

settings = Settings()
