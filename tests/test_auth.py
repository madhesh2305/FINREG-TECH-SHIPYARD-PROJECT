from fastapi.testclient import TestClient
from app.db.session import SessionLocal
from app.models.identity import User

def test_login_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jun@finregtech.io", "password": "Password123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "jun@finregtech.io"
    assert data["full_name"] == "Jun Chen"
    assert data["platform_role"] == "BUILDER"
    assert data["expires_in"] > 0

def test_login_invalid_password(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jun@finregtech.io", "password": "WrongPassword999!"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@finregtech.io", "password": "Password123!"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_get_current_user_me(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/users/me", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jun@finregtech.io"
    assert data["full_name"] == "Jun Chen"
    assert data["platform_role"] == "BUILDER"
    assert data["is_active"] is True

def test_get_current_user_no_token(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_get_current_user_invalid_token(client: TestClient):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert response.status_code == 401

def test_inactive_user_cannot_login(client: TestClient):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "jun@finregtech.io").first()
        user.is_active = False
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "jun@finregtech.io", "password": "Password123!"}
        )
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()
    finally:
        # Re-activate user
        user.is_active = True
        db.commit()
        db.close()
