import uuid
from fastapi.testclient import TestClient

def test_outsider_cannot_access_project_endpoints(client: TestClient, outsider_auth_headers: dict):
    # 1. Project details
    resp = client.get("/api/v1/projects/1", headers=outsider_auth_headers)
    assert resp.status_code == 403

    # 2. Members
    resp = client.get("/api/v1/projects/1/members", headers=outsider_auth_headers)
    assert resp.status_code == 403

    # 3. Requirements
    resp = client.get("/api/v1/projects/1/requirements", headers=outsider_auth_headers)
    assert resp.status_code == 403

    # 4. Audit events
    resp = client.get("/api/v1/projects/1/audit-events", headers=outsider_auth_headers)
    assert resp.status_code == 403

    # 5. AI retrieve
    resp = client.post("/api/v1/projects/1/ai/retrieve", json={"query": "test"}, headers=outsider_auth_headers)
    assert resp.status_code == 403

def test_platform_admin_cannot_bypass_project_isolation(client: TestClient, admin_auth_headers: dict):
    """
    Platform ADMIN does NOT automatically bypass project-level isolation.
    Admin must have an explicit project membership to access project data.
    """
    resp = client.get("/api/v1/projects/1", headers=admin_auth_headers)
    assert resp.status_code == 403
    assert "not an active member" in resp.json()["detail"].lower()

def test_nested_object_bola_idor_defense(client: TestClient, builder_auth_headers: dict):
    """
    IDOR / BOLA Defense:
    Create a second project where Jun is owner, and try to access Project 1's requirement
    using Project 2's route: /projects/{project2_id}/requirements/{project1_req_id}
    Must return 404.
    """
    unique_code = f"PRJ-IDOR-{uuid.uuid4().hex[:4].upper()}"
    p2_resp = client.post(
        "/api/v1/projects",
        json={
            "project_name": "Second Project for BOLA Test",
            "project_code": unique_code,
            "description": "BOLA testing",
            "jurisdiction": "UK",
            "regulatory_scope": "Testing",
            "objectives": "Testing"
        },
        headers=builder_auth_headers
    )
    assert p2_resp.status_code == 201
    p2_id = p2_resp.json()["project_id"]

    # Requirement 1 belongs to Project 1. Jun is member of Project 2.
    # Attempting to access requirement 1 via Project 2 path:
    idor_resp = client.get(f"/api/v1/projects/{p2_id}/requirements/1", headers=builder_auth_headers)
    assert idor_resp.status_code == 404
    assert "not found in this project" in idor_resp.json()["detail"].lower()

def test_advisor_cannot_be_assigned_owner_role(client: TestClient, builder_auth_headers: dict):
    """
    Platform ADVISOR cannot be assigned the project OWNER role.
    """
    # Eleanor Vance (user_id 2) is platform ADVISOR
    payload = {
        "user_id": 2,
        "service_role": "OWNER"
    }
    resp = client.post("/api/v1/projects/1/members", json=payload, headers=builder_auth_headers)
    assert resp.status_code == 403
    assert "advisor cannot be assigned the project owner role" in resp.json()["detail"].lower()
