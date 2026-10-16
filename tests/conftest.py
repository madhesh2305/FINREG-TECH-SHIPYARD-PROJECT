import os
import sys
from urllib.parse import unquote
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, Session

# Ensure backend root is on Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.base import Base
import app.models  # Register all domain models
import app.db.session as db_session_module
from app.db.session import get_db
from app.main import app
from app.models.identity import User, Role
from app.core.security import get_password_hash
from scripts.seed_data import seed_database

# ---------------------------------------------------------------------------
# Test Database Resolution & Strict Isolation Guard
# ---------------------------------------------------------------------------
TEST_DB_URL = os.getenv("TEST_DATABASE_URL") or settings.TEST_DATABASE_URL
if not TEST_DB_URL:
    TEST_DB_URL = "sqlite:///./test_finregtech.db"

# Verify test database is NEVER the shared development/production database
parsed_test = make_url(TEST_DB_URL)
test_db_name = parsed_test.database
if test_db_name:
    decoded_name = unquote(test_db_name)
    assert decoded_name != "FinRegTech ShipYard", (
        "CRITICAL ERROR: Tests must NOT run against the primary 'FinRegTech ShipYard' database! "
        "Configure TEST_DATABASE_URL to an isolated test database (e.g. finregtech_test)."
    )

# Build isolated test engine
if TEST_DB_URL.startswith("sqlite"):
    test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
else:
    if test_db_name and "%20" in test_db_name:
        parsed_test = parsed_test.set(database=unquote(test_db_name))
    test_engine = create_engine(parsed_test, pool_pre_ping=True)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Monkeypatch database session module globals so direct imports use the test database
db_session_module.engine = test_engine
db_session_module.SessionLocal = TestSessionLocal

# FastAPI Dependency Override
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is created and seeded in the isolated test database."""
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()
    try:
        seed_database(session_override=db, engine_override=test_engine)

        # Ensure outsider builder exists in test database
        builder_role = db.query(Role).filter(Role.role_name == "BUILDER").first()
        outsider = db.query(User).filter(User.email == "outsider@finregtech.io").first()
        if not outsider and builder_role:
            outsider = User(
                email="outsider@finregtech.io",
                password_hash=get_password_hash("Password123!"),
                full_name="Outsider Builder",
                role_id=builder_role.role_id,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(outsider)
            db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    """Yield an isolated test database session per test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def _get_token(client: TestClient, email: str, password: str = "Password123!") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Failed to login as {email}: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture
def builder_auth_headers(client):
    token = _get_token(client, "jun@finregtech.io")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def advisor_auth_headers(client):
    token = _get_token(client, "eleanor.vance@vancelegal.co.uk")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client):
    token = _get_token(client, "admin@finregtech.io")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def outsider_auth_headers(client):
    token = _get_token(client, "outsider@finregtech.io")
    return {"Authorization": f"Bearer {token}"}
