import uuid
from fastapi.testclient import TestClient

def test_register_builder_success(client: TestClient):
    unique_email = f"builder_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Test Builder User",
        "role": "BUILDER"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["email"] == unique_email
    assert data["full_name"] == "Test Builder User"
    assert data["platform_role"] == "BUILDER"

    # Verify token works for /users/me
    token = data["access_token"]
    me_resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == unique_email

def test_register_advisor_success(client: TestClient):
    unique_email = f"advisor_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Test Advisor User",
        "role": "ADVISOR",
        "organization": "Apex Regulatory Advisory Ltd"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["platform_role"] == "ADVISOR"

def test_register_duplicate_email(client: TestClient):
    payload = {
        "email": "jun@finregtech.io",
        "password": "Password123!",
        "full_name": "Duplicate Jun",
        "role": "BUILDER"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()

def test_register_invalid_role(client: TestClient):
    payload = {
        "email": f"invalid_{uuid.uuid4().hex[:8]}@example.com",
        "password": "Password123!",
        "full_name": "Invalid Role User",
        "role": "SUPERUSER"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422

def test_login_with_demo_credentials(client: TestClient):
    # Test builder@gmail.com
    resp1 = client.post("/api/v1/auth/login", json={"email": "builder@gmail.com", "password": "builder"})
    assert resp1.status_code == 200
    assert resp1.json()["platform_role"] == "BUILDER"

    # Test advisor@gmail.com
    resp2 = client.post("/api/v1/auth/login", json={"email": "advisor@gmail.com", "password": "advisor"})
    assert resp2.status_code == 200
    assert resp2.json()["platform_role"] == "ADVISOR"
