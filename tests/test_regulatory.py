import uuid
from fastapi.testclient import TestClient

def test_list_regulatory_sources(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/regulatory/sources", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 18
    assert len(data["items"]) >= 1

def test_filter_regulatory_sources(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/regulatory/sources?jurisdiction=UK", headers=builder_auth_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert all("UK" in s["jurisdiction"] for s in items)

def test_get_regulatory_source_by_id(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/regulatory/sources/1", headers=builder_auth_headers)
    assert response.status_code == 200
    source = response.json()
    assert source["source_id"] == 1
    assert "source_title" in source
    assert "source_url" in source
    assert source["validation_status"] == "VALIDATED"

def test_list_project_requirements(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/1/requirements", headers=builder_auth_headers)
    assert response.status_code == 200
    reqs = response.json()
    assert isinstance(reqs, list)
    assert len(reqs) >= 8
    assert any(r["requirement_code"] == "REQ-ABC-001" for r in reqs)

def test_create_and_patch_requirement(client: TestClient, builder_auth_headers: dict):
    unique_code = f"REQ-TEST-{uuid.uuid4().hex[:4].upper()}"
    payload = {
        "source_id": 1,
        "requirement_code": unique_code,
        "requirement_title": "Automated Beneficial Ownership Verification Hook",
        "requirement_text": "Verify PSC registers via automated Companies House API connector.",
        "applicability_status": "APPLICABLE",
        "requirement_status": "OPEN"
    }
    # 1. Create requirement
    response = client.post("/api/v1/projects/1/requirements", json=payload, headers=builder_auth_headers)
    assert response.status_code == 201
    req = response.json()
    assert req["requirement_code"] == unique_code
    req_id = req["requirement_id"]

    # 2. Patch requirement
    patch_resp = client.patch(
        f"/api/v1/projects/1/requirements/{req_id}",
        json={"requirement_status": "COMPLETED"},
        headers=builder_auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["requirement_status"] == "COMPLETED"

def test_provenance_validation_rejects_unapproved_source(client: TestClient, builder_auth_headers: dict):
    payload = {
        "source_id": 99999,  # Non-existent source
        "requirement_code": f"REQ-FAIL-{uuid.uuid4().hex[:4].upper()}",
        "requirement_title": "Requirement with fabricated source",
        "requirement_text": "This should fail provenance validation."
    }
    response = client.post("/api/v1/projects/1/requirements", json=payload, headers=builder_auth_headers)
    assert response.status_code == 404
    assert "source" in response.json()["detail"].lower()
