from fastapi.testclient import TestClient

def test_ai_grounded_retrieval_success(client: TestClient, builder_auth_headers: dict):
    payload = {
        "query": "Customer Due Diligence CDD verification procedures",
        "top_k": 3
    }
    response = client.post("/api/v1/projects/1/ai/retrieve", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "GROUNDED_EVIDENCE_FOUND"
    assert len(data["citations"]) > 0
    assert "disclaimer" in data
    # Verify citations are real objects with URLs
    for cit in data["citations"]:
        assert cit["source_url"].startswith("http")
        assert cit["topic"] is not None

def test_ai_grounded_retrieval_no_match(client: TestClient, builder_auth_headers: dict):
    payload = {
        "query": "quantum mechanical propulsion orbital mechanics",
        "top_k": 3
    }
    response = client.post("/api/v1/projects/1/ai/retrieve", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NO_SOURCE_FOUND"
    assert len(data["citations"]) == 0

def test_audit_events_retrieval(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/1/audit-events", headers=builder_auth_headers)
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    # Check structure
    event = events[0]
    assert "audit_event_id" in event
    assert "event_type" in event
    assert "event_description" in event
    assert "created_at" in event

def test_rag_analyze_conflict(client: TestClient, builder_auth_headers: dict):
    payload = {
        "query": "Compare advisor recommendations on data retention against FCA guidelines"
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["status"] == "CONFLICT_DETECTED"
    assert data["grounded"] is True
    assert len(data["conflicts"]) > 0
    assert len(data["citations"]) > 0
    assert len(data["provenance"]) > 0
    assert "disclaimer" in data["metadata"]

def test_rag_analyze_project_scoped_query(client: TestClient, builder_auth_headers: dict):
    payload = {
        "query": "Customer onboarding identity verification procedures",
        "projectId": 1
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["schema_version"] == "1.0"
    assert "status" in data
    assert "citations" in data
    assert "metadata" in data
    assert "disclaimer" in data["metadata"]

def test_project_readiness_calculation(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/1/readiness", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "readiness_percentage" in data
    assert "readiness_score" in data
    assert "readiness_status" in data
    assert "breakdown" in data
    assert len(data["breakdown"]) == 3

def test_project_access_by_code(client: TestClient, builder_auth_headers: dict):
    response = client.get("/api/v1/projects/PRJ-ABC-001", headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["project_code"] == "PRJ-ABC-001"
    assert data["id"] == 1
    assert data["name"] == "ABC Shield Compliance Infrastructure (Updated)" or "ABC Shield" in data["name"]
