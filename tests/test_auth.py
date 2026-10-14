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

def test_patch_current_user_me(client: TestClient, builder_auth_headers: dict):
    # Test update
    response = client.patch(
        "/api/v1/users/me",
        headers=builder_auth_headers,
        json={"full_name": "Jun Chen Updated"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Jun Chen Updated"
    assert data["email"] == "jun@finregtech.io"

    # Restore original name
    restore_resp = client.patch(
        "/api/v1/users/me",
        headers=builder_auth_headers,
        json={"full_name": "Jun Chen"}
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["full_name"] == "Jun Chen"

def test_change_password_endpoint(client: TestClient, builder_auth_headers: dict):
    # 1. Reject incorrect current password
    bad_res = client.post(
        "/api/v1/auth/change-password",
        headers=builder_auth_headers,
        json={"current_password": "WrongPassword123!", "new_password": "BrandNewPassword123!"}
    )
    assert bad_res.status_code == 401

    # 2. Accept correct current password
    good_res = client.post(
        "/api/v1/auth/change-password",
        headers=builder_auth_headers,
        json={"current_password": "Password123!", "new_password": "BrandNewPassword123!"}
    )
    assert good_res.status_code == 200
    assert good_res.json()["status"] == "success"

    # 3. Verify login works with new password
    login_new = client.post(
        "/api/v1/auth/login",
        json={"email": "jun@finregtech.io", "password": "BrandNewPassword123!"}
    )
    assert login_new.status_code == 200
    new_token = login_new.json()["access_token"]

    # 4. Restore original password
    restore_res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {new_token}"},
        json={"current_password": "BrandNewPassword123!", "new_password": "Password123!"}
    )
    assert restore_res.status_code == 200

def test_password_reset_request_truthful_response(client: TestClient):
    res = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": "jun@finregtech.io"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_configuration"
    assert "SMTP" in data["delivery_channel"]
    assert "unconfigured" in data["message"].lower()

def test_get_user_notifications(client: TestClient, builder_auth_headers: dict):
    res = client.get("/api/v1/users/me/notifications", headers=builder_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

