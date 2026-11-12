import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_docs_accessible_in_development():
    """Verify interactive docs and openapi are available when not in production."""
    assert settings.ENVIRONMENT != "production"

    # 1. Root index lists doc URLs
    res_root = client.get("/")
    assert res_root.status_code == 200
    data = res_root.json()
    assert data.get("docs_url") == "/docs"
    assert data.get("openapi_url") == "/openapi.json"

    # 2. OpenAPI schemas are served
    res_api_v1_openapi = client.get("/api/v1/openapi.json")
    assert res_api_v1_openapi.status_code == 200
    assert "paths" in res_api_v1_openapi.json()


def test_openapi_disabled_in_production():
    """Verify OpenAPI and documentation endpoints are suppressed when ENVIRONMENT is production."""
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"

        # 1. Root index suppresses doc URLs
        res_root = client.get("/")
        assert res_root.status_code == 200
        data = res_root.json()
        assert data.get("docs_url") is None
        assert data.get("redoc_url") is None
        assert data.get("openapi_url") is None

        # 2. Direct request to /api/v1/openapi.json returns 404
        res_api_v1_openapi = client.get("/api/v1/openapi.json")
        assert res_api_v1_openapi.status_code == 404
        assert "disabled in production" in res_api_v1_openapi.json().get("detail", "")

    finally:
        settings.ENVIRONMENT = original_env


def test_requirements_lock_integrity():
    """Verify requirements.lock exists, contains exact pinned versions, and contains no secrets."""
    backend_root = Path(__file__).resolve().parent.parent
    lock_file = backend_root / "requirements.lock"
    assert lock_file.exists(), "requirements.lock must exist"

    content = lock_file.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    # Verify all entries are pinned with exact == versions
    assert len(lines) > 20, f"Expected > 20 locked dependencies, got {len(lines)}"
    for line in lines:
        assert "==" in line, f"Dependency line '{line}' is not pinned with exact '==' version"

    # Verify core required packages are locked
    locked_text = content.lower()
    for core_pkg in ["fastapi==", "sqlalchemy==", "pydantic==", "pyjwt==", "bcrypt==", "pypdf=="]:
        assert core_pkg in locked_text, f"Core package {core_pkg} missing from lockfile"

    # Verify no local credentials or paths are present
    assert "password" not in locked_text
    assert "secret" not in locked_text
    assert "c:\\" not in locked_text
    assert "file://" not in locked_text
