from fastapi.testclient import TestClient

def test_record_decision_success(client: TestClient, builder_auth_headers: dict):
    payload = {
        "decision_type": "ACCEPT",
        "decision_rationale": "Accepted advisor recommendation to enforce mandatory EDD on ownership structures exceeding 25%.",
        "follow_up_action": "Incorporate enhanced threshold checks in Sprint 5 onboarding pipeline."
    }
    response = client.post("/api/v1/projects/1/decisions", json=payload, headers=builder_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["decision_type"] == "ACCEPT"
    assert data["decision_rationale"] == payload["decision_rationale"]
    assert data["follow_up_action"] == payload["follow_up_action"]
    assert data["decider_name"] == "Jun Chen"
    assert data["project_id"] == 1

def test_list_and_get_decisions(client: TestClient, builder_auth_headers: dict):
    # List decisions
    response = client.get("/api/v1/projects/1/decisions", headers=builder_auth_headers)
    assert response.status_code == 200
    decisions = response.json()
    assert isinstance(decisions, list)
    assert len(decisions) >= 1

    # Get single decision
    dec_id = decisions[0]["decision_id"]
    single_resp = client.get(f"/api/v1/projects/1/decisions/{dec_id}", headers=builder_auth_headers)
    assert single_resp.status_code == 200
    assert single_resp.json()["decision_id"] == dec_id

def test_invalid_decision_type(client: TestClient, builder_auth_headers: dict):
    payload = {
        "decision_type": "MAYBE_ACCEPT",
        "decision_rationale": "Invalid decision type test."
    }
    response = client.post("/api/v1/projects/1/decisions", json=payload, headers=builder_auth_headers)
    assert response.status_code == 422

def test_advisor_cannot_record_decision(client: TestClient, advisor_auth_headers: dict):
    # Eleanor Vance (ADVISOR) is not OWNER
    payload = {
        "decision_type": "ACCEPT",
        "decision_rationale": "Advisors cannot make executive decisions."
    }
    response = client.post("/api/v1/projects/1/decisions", json=payload, headers=advisor_auth_headers)
    assert response.status_code == 403
    assert "service role: owner" in response.json()["detail"].lower()

def test_outsider_cannot_access_decisions(client: TestClient, outsider_auth_headers: dict):
    response = client.get("/api/v1/projects/1/decisions", headers=outsider_auth_headers)
    assert response.status_code == 403

def test_decision_creates_audit_log(client: TestClient, builder_auth_headers: dict):
    # Record another decision
    payload = {
        "decision_type": "REVIEW_REQUIRED",
        "decision_rationale": "Review required on transaction monitoring false positive threshold.",
        "follow_up_action": "Schedule FCC alignment meeting."
    }
    client.post("/api/v1/projects/1/decisions", json=payload, headers=builder_auth_headers)

    # Check audit events
    audit_resp = client.get("/api/v1/projects/1/audit-events", headers=builder_auth_headers)
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    assert any(e["event_type"] == "DECISION_RECORDED" for e in events)
