import os
import sys
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

# Ensure backend root is on Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db.session import engine, SessionLocal
from app.models.identity import User, Role
from app.core.security import get_password_hash
from scripts.seed_data import seed_database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema is created and seeded before running test suite."""
    seed_database()
    
    # Create an outsider builder who is NOT a member of ABC Shield (project 1)
    db = SessionLocal()
    try:
        builder_role = db.query(Role).filter(Role.role_name == "BUILDER").first()
        outsider = db.query(User).filter(User.email == "outsider@finregtech.io").first()
        if not outsider:
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
