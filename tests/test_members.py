from fastapi.testclient import TestClient

def test_list_project_members(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/1/members", headers=builder_auth_headers)
    assert response.status_code == 200
    members = response.json()
    assert isinstance(members, list)
    assert len(members) >= 1
    assert any(m["service_role"] == "OWNER" for m in members)

def test_add_and_update_member(client: TestClient, builder_auth_headers: dict):
    # Eleanor Vance (user_id 2) added as LEGAL
    payload = {
        "user_id": 2,
        "service_role": "LEGAL",
        "service_scope": "LEGAL_ADVICE_SUPPORT"
    }
    response = client.post("/api/v1/projects/1/members", json=payload, headers=builder_auth_headers)
    # May be 201 or if previously added, check result
    assert response.status_code in (201, 409)

    if response.status_code == 201:
        member = response.json()
        assert member["service_role"] == "LEGAL"
        member_id = member["project_member_id"]

        # Update member scope
        update_resp = client.patch(
            f"/api/v1/projects/1/members/{member_id}",
            json={"service_scope": "EXPANDED_LEGAL_SUPPORT"},
            headers=builder_auth_headers
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["service_scope"] == "EXPANDED_LEGAL_SUPPORT"

def test_outsider_cannot_manage_members(client: TestClient, outsider_auth_headers: dict):
    response = client.get("/api/v1/projects/1/members", headers=outsider_auth_headers)
    assert response.status_code == 403

    response = client.post(
        "/api/v1/projects/1/members",
        json={"user_id": 3, "service_role": "TECH"},
        headers=outsider_auth_headers
    )
    assert response.status_code == 403

def test_sole_owner_cannot_be_revoked(client: TestClient, builder_auth_headers: dict):
    members = client.get("/api/v1/projects/1/members", headers=builder_auth_headers).json()
    owner_member = next(m for m in members if m["service_role"] == "OWNER")

    response = client.delete(f"/api/v1/projects/1/members/{owner_member['project_member_id']}", headers=builder_auth_headers)
    assert response.status_code == 403
    assert "sole project owner" in response.json()["detail"].lower()
