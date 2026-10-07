import uuid
from fastapi.testclient import TestClient

def test_list_projects(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects", headers=builder_auth_headers)
    assert response.status_code == 200
    projects = response.json()
    assert isinstance(projects, list)
    assert len(projects) >= 1
    assert any(p["project_code"] == "PRJ-ABC-001" for p in projects)

def test_create_project(client: TestClient, builder_auth_headers: dict):
    unique_code = f"PRJ-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "project_name": "NextGen PayTech Compliance",
        "project_code": unique_code,
        "description": "Compliance setup for pan-European PSP",
        "jurisdiction": "UK / EU",
        "regulatory_scope": "MLR 2017, 5AMLD, PSR 2017",
        "objectives": "Achieve full regulatory audit readiness before Q3."
    }
    response = client.post("/api/v1/projects", json=payload, headers=builder_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["project_code"] == unique_code
    assert data["status"] == "ACTIVE"
    assert data["profile"] is not None
    assert data["profile"]["jurisdiction"] == "UK / EU"

    # Verify project appears in list
    list_resp = client.get("/api/v1/projects", headers=builder_auth_headers)
    assert any(p["project_code"] == unique_code for p in list_resp.json())

def test_get_project_details(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/1", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == 1
    assert data["project_code"] == "PRJ-ABC-001"
    assert data["profile"]["jurisdiction"] == "UK"

def test_patch_project_details(client: TestClient, builder_auth_headers: dict):
    payload = {
        "project_name": "ABC Shield Compliance Infrastructure (Updated)",
        "regulatory_scope": "UK MLR 2017, FCA SYSC, POCA 2002, TACT 2000"
    }
    response = client.patch("/api/v1/projects/1", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_name"] == "ABC Shield Compliance Infrastructure (Updated)"
    assert data["profile"]["regulatory_scope"] == "UK MLR 2017, FCA SYSC, POCA 2002, TACT 2000"

def test_dashboard_summary(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/summary", headers=builder_auth_headers)
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_projects"] >= 1
    assert summary["active_projects"] >= 1
    assert summary["total_requirements"] >= 8
    assert summary["total_members"] >= 1

def test_outsider_cannot_access_project(client: TestClient, outsider_auth_headers: dict):
    # Outsider tries to access Project 1 (where only Jun is member)
    response = client.get("/api/v1/projects/1", headers=outsider_auth_headers)
    assert response.status_code == 403
    assert "not an active member" in response.json()["detail"].lower()
