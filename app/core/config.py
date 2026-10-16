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

    DATABASE_URL: str = "postgresql://postgres:vishal1516@localhost:5432/FinRegTech%20ShipYard"
    SQLITE_FALLBACK_URL: str = "sqlite:///./finregtech_dev.db"

    SECRET_KEY: str = "finregtech-shipyard-secret-key-change-in-production-min-32-bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    model_config = SettingsConfigDict(
        env_file=[_backend_env, ".env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
