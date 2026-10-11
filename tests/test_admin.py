import pytest
from fastapi.testclient import TestClient

def test_admin_stats_authorized(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/admin/stats", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "active_users" in data
    assert "total_projects" in data
    assert "regulatory_sources_count" in data
    assert data["total_users"] >= 1
    assert data["regulatory_sources_count"] >= 18

def test_admin_users_list(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1
    assert any(u["email"] == "admin@finregtech.io" for u in users)

def test_admin_toggle_user_status(client: TestClient, admin_auth_headers: dict):
    # Find a non-admin user
    users_resp = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    non_admin = next(u for u in users_resp.json() if u["email"] != "admin@finregtech.io")
    uid = non_admin["user_id"]
    original_status = non_admin["is_active"]

    # Toggle
    patch_resp = client.patch(
        f"/api/v1/admin/users/{uid}/status",
        json={"is_active": not original_status},
        headers=admin_auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_active"] == (not original_status)

    # Revert back
    revert_resp = client.patch(
        f"/api/v1/admin/users/{uid}/status",
        json={"is_active": original_status},
        headers=admin_auth_headers
    )
    assert revert_resp.status_code == 200
    assert revert_resp.json()["is_active"] == original_status

def test_admin_endpoints_reject_builder(client: TestClient, builder_auth_headers: dict):
    resp1 = client.get("/api/v1/admin/stats", headers=builder_auth_headers)
    assert resp1.status_code == 403

    resp2 = client.get("/api/v1/admin/users", headers=builder_auth_headers)
    assert resp2.status_code == 403

def test_admin_endpoints_reject_unauthenticated(client: TestClient):
    resp = client.get("/api/v1/admin/stats")
    assert resp.status_code == 401
