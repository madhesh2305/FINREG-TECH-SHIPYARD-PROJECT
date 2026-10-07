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
