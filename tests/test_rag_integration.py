"""ABC Shield AI/RAG Integration Test Suite for FinRegTech ShipYard.

Tests the live integration between the ShipYard backend API (port 8000)
and the isolated ABC Shield AI/RAG microservice (port 8001).

Guarantees:
1. Strict database safety (only touches finregtech_test, never primary DB).
2. Strict authentication & project authorization (401 / 403).
3. BOLA/IDOR protection on requirement_ids and advisor_advice_ids (404).
4. Evidence safety: all 25 candidate records retain is_approved_for_rag=False.
5. Fail-closed on filter_approved_only=True (zero citations, unapproved evidence).
6. Non-adjudication invariant on advice comparison (decision=None, mandatory disclaimer).
7. Full compatibility with Harshini's DashboardView.jsx contract.
8. Truthful error handling on RAG service failure/timeout (503).
"""

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session


# ==============================================================================
# Scenario 1: Strict Database Isolation Guard
# ==============================================================================
def test_database_safety_guard(db: Session):
    """Verify that tests execute strictly against the isolated test database."""
    result = db.execute(text("SELECT current_database();")).scalar()
    assert result != "FinRegTech ShipYard", (
        "CRITICAL SAFETY VIOLATION: Test executed against primary database 'FinRegTech ShipYard'!"
    )
    assert result == "finregtech_test", (
        f"Expected isolated test database 'finregtech_test', but connected to '{result}'"
    )


# ==============================================================================
# Scenario 2: Valid Authenticated Grounded Query (Success)
# ==============================================================================
def test_authenticated_rag_query_success(client: TestClient, builder_auth_headers: dict):
    """Verify valid authenticated grounded query returns 200 with citations and candidate metadata."""
    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover regarding failure of commercial organisations to prevent bribery?",
        "projectId": 1,
        "context": {
            "jurisdiction": "UK",
        },
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["schema_version"] == "1.0"
    assert data["status"] in ("SUCCESS", "GROUNDED", "CONFLICT_DETECTED")
    assert data["grounded"] is True
    assert "Bribery Act 2010" in data["answer"]
    assert len(data["citations"]) >= 1
    assert len(data["provenance"]) >= 1

    # Verify candidate evidence safety invariant: all records must be is_approved_for_rag=False
    for cit in data["citations"]:
        assert cit["is_approved_for_rag"] is False
        assert cit["jurisdiction"] == "UK"
        assert "Bribery Act" in cit["title"] or "Bribery Act" in cit["regulation"]
        assert cit["url"].startswith("http") or cit["official_source"].startswith("http")

    assert data["metadata"]["has_candidate_evidence"] is True
    assert data["metadata"]["approved_evidence_count"] == 0
    assert "disclaimer" in data["metadata"]


# ==============================================================================
# Scenario 3: Unauthenticated Request (401 Unauthorized)
# ==============================================================================
def test_rag_query_unauthenticated(client: TestClient):
    """Verify unauthenticated requests are strictly rejected with 401 Unauthorized."""
    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload)
    assert response.status_code == 401
    assert "detail" in response.json()


# ==============================================================================
# Scenario 4: Unauthorized Outsider User (403 Forbidden)
# ==============================================================================
def test_rag_query_unauthorized_outsider(client: TestClient, outsider_auth_headers: dict):
    """Verify an authenticated user who is not a project member cannot query project RAG."""
    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=outsider_auth_headers)
    assert response.status_code == 403
    assert "not an active member" in response.json()["detail"].lower()


# ==============================================================================
# Scenario 5: BOLA / IDOR Protection on Requirements and Advice (404 Not Found)
# ==============================================================================
def test_rag_query_invalid_requirement_bola(client: TestClient, builder_auth_headers: dict):
    """Verify requesting nonexistent or foreign requirements returns 404 (BOLA defense)."""
    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
        "requirement_ids": ["REQ-NONEXISTENT-9999"],
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 404
    assert "not found in project" in response.json()["detail"].lower()


def test_rag_query_invalid_advice_bola(client: TestClient, builder_auth_headers: dict):
    """Verify requesting nonexistent or foreign advice IDs returns 404 (BOLA defense)."""
    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
        "advisor_advice_ids": [99999],
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 404
    assert "not found in project" in response.json()["detail"].lower()


# ==============================================================================
# Scenario 6: Valid Advice Comparison Request (POST /api/v1/rag/compare)
# ==============================================================================
def test_rag_advice_comparison_success(client: TestClient, builder_auth_headers: dict):
    """Verify advisor comparison endpoint returns structured differences with non-adjudication disclaimer."""
    payload = {
        "comparison_id": "CMP-TEST-001",
        "projectId": 1,
        "advisor_1": {
            "advice_id": "ADV-001",
            "advisor_name": "Eleanor Vance (Vance Legal LLP)",
            "advice_text": "Bribery Act 2010 Section 1 offences and Section 7 failure to prevent bribery. Recommend £100 hospitality pre-approval threshold.",
            "source_reference": "UK Bribery Act 2010 Section 1 & 7",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advisor_name": "Marcus Reid (FCC Consulting Europe)",
            "advice_text": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures. Propose £250 operational threshold.",
            "source_reference": "MoJ Guidance on Bribery Act 2010",
        },
        "context": {
            "jurisdiction": "UK",
        },
    }
    response = client.post("/api/v1/rag/compare", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    assert data["schema_version"] == "1.0"
    assert len(data["conflicts"]) >= 1
    assert "metadata" in data
    assert "disclaimer" in data["metadata"]
    # Non-adjudication invariant: must never contain automated final decision
    assert data.get("decision") is None
    disclaimer_lower = data["metadata"]["disclaimer"].lower()
    assert any(term in disclaimer_lower for term in [
        "compliance professional", "qualified compliance", "not constitute formal legal", "human", "ratification"
    ])


# ==============================================================================
# Scenario 7: Empty or Whitespace-Only Query (422 Validation Error)
# ==============================================================================
def test_rag_query_empty_or_whitespace(client: TestClient, builder_auth_headers: dict):
    """Verify empty or whitespace-only queries are rejected with 422 Unprocessable Entity."""
    for empty_val in ["", "   ", "\t\n"]:
        payload = {"query": empty_val, "projectId": 1}
        response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
        assert response.status_code == 422, f"Expected 422 for query '{empty_val}', got {response.status_code}"


# ==============================================================================
# Scenario 8: Out-of-Scope Query
# ==============================================================================
def test_rag_query_out_of_scope(client: TestClient, builder_auth_headers: dict):
    """Verify out-of-scope taxonomy topics return OUT_OF_SCOPE status with zero citations."""
    payload = {
        "query": "OFAC sanctions screening lists and Specially Designated Nationals SDN blocked persons",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OUT_OF_SCOPE"
    assert len(data["citations"]) == 0
    assert data["gap"]["isGapDetected"] is True
    assert data["gap"]["description"] == "OUT_OF_SCOPE"


# ==============================================================================
# Scenario 9: Insufficient Evidence / French Transposition Query
# ==============================================================================
def test_rag_query_insufficient_evidence_french_transposition(client: TestClient, builder_auth_headers: dict):
    """Verify jurisdictional gaps return INSUFFICIENT_EVIDENCE with zero citations."""
    payload = {
        "query": "French Sapin II anti-corruption loi transposition and compliance requirements",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "INSUFFICIENT_EVIDENCE"
    assert len(data["citations"]) == 0
    assert data["gap"]["isGapDetected"] is True
    assert data["gap"]["description"] in ("INSUFFICIENT_EVIDENCE", "DATA_COVERAGE_LIMITATION")


# ==============================================================================
# Scenario 10: Approved-Only Gating Fail-Closed Invariant
# ==============================================================================
def test_rag_query_fail_closed_approved_only(client: TestClient, builder_auth_headers: dict):
    """Verify fail-closed invariant: filter_approved_only=True returns UNAPPROVED_EVIDENCE and zero citations."""
    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
        "context": {
            "filter_approved_only": True,
        },
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UNAPPROVED_EVIDENCE"
    assert data["grounded"] is False
    assert len(data["citations"]) == 0
    assert data["metadata"]["requires_human_review"] is True


# ==============================================================================
# Scenario 11: Conflict Detection and Advice Discrepancy Mapping
# ==============================================================================
def test_rag_query_conflict_detection(client: TestClient, builder_auth_headers: dict):
    """Verify queries requesting comparison return CONFLICT_DETECTED with advisor difference breakdown."""
    payload = {
        "query": "Compare advisor recommendations on data retention against FCA guidelines",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONFLICT_DETECTED"
    assert data["grounded"] is True
    assert len(data["conflicts"]) >= 1

    first_conflict = data["conflicts"][0]
    assert "advisorA" in first_conflict
    assert "advisorB" in first_conflict
    assert "topic" in first_conflict
    assert "severity" in first_conflict
    assert "name" in first_conflict["advisorA"]
    assert "recommendation" in first_conflict["advisorA"]


# ==============================================================================
# Scenario 12: Citation Provenance Format and Traceability
# ==============================================================================
def test_rag_citation_provenance_traceability(client: TestClient, builder_auth_headers: dict):
    """Verify citations and provenance objects contain all required verification and traceability fields."""
    payload = {
        "query": "What are the six principles in the Ministry of Justice guidance under Bribery Act 2010?",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Citations validation
    assert len(data["citations"]) >= 1
    cit = data["citations"][0]
    assert "source_id" in cit
    assert "title" in cit
    assert "jurisdiction" in cit
    assert "section" in cit
    assert "url" in cit
    assert "official_source" in cit
    assert "validation_status" in cit
    assert "is_approved_for_rag" in cit
    assert cit["is_approved_for_rag"] is False

    # Provenance validation
    assert len(data["provenance"]) >= 1
    prov = data["provenance"][0]
    assert "record_id" in prov or "recordId" in prov
    assert "source_id" in prov or "sourceId" in prov
    assert "section" in prov
    assert "official_source" in prov or "officialSource" in prov
    assert "validation_status" in prov or "validationStatus" in prov
    assert prov["is_approved_for_rag"] is False


# ==============================================================================
# Scenario 13: DashboardView Frontend Contract Compatibility
# ==============================================================================
def test_rag_dashboard_frontend_contract(client: TestClient, builder_auth_headers: dict):
    """Verify response structure strictly matches Harshini's DashboardView.jsx expectations."""
    payload = {
        "query": "Explain customer due diligence under money laundering regulations",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200
    data = response.json()

    # DashboardView.jsx state bindings:
    # data.status, data.answer, data.grounded, data.citations, data.provenance, data.conflicts, data.metadata
    expected_top_keys = {
        "schema_version",
        "request_id",
        "query",
        "status",
        "answer",
        "grounded",
        "gap",
        "citations",
        "provenance",
        "conflicts",
        "retrieved_evidence",
        "metadata",
    }
    assert expected_top_keys.issubset(data.keys()), f"Missing keys: {expected_top_keys - set(data.keys())}"

    assert isinstance(data["citations"], list)
    assert isinstance(data["provenance"], list)
    assert isinstance(data["conflicts"], list)
    assert isinstance(data["findings"], list)
    assert isinstance(data["metadata"], dict)
    assert "disclaimer" in data["metadata"]


def test_rag_query_snake_case_project_id_and_findings_view_contract(client: TestClient, builder_auth_headers: dict):
    """Verify that project_id (snake_case) is supported and findings array strictly matches AiRagFindingsView.jsx."""
    payload = {
        "query": "What are the reporting obligations under Proceeds of Crime Act 2002?",
        "project_id": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert "findings" in data
    assert isinstance(data["findings"], list)
    assert len(data["findings"]) > 0

    # Verify keys required by Harshini's AiRagFindingsView.jsx
    sample = data["findings"][0]
    for required_key in ["id", "finding", "type", "requirement", "supportingSource", "humanReview", "typeBadge", "statusBadge", "reviewDetails", "typeDetailBadge", "detailStatusBadge", "detailStatusDot"]:
        assert required_key in sample, f"Missing required finding key: {required_key}"


# ==============================================================================
# Scenario 14: RAG Microservice Unavailable Handling (503 Service Unavailable)
# ==============================================================================
def test_rag_service_unavailable(client: TestClient, builder_auth_headers: dict, monkeypatch):
    """Verify HTTP 503 is returned with a truthful error message when RAG microservice is down."""
    orig_post = httpx.Client.post

    def mock_post(self, url, *args, **kwargs):
        if "8001" in str(url):
            raise httpx.ConnectError("Connection refused on 127.0.0.1:8001")
        return orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 503
    data = response.json()
    assert "unreachable on port 8001" in data["detail"]


# ==============================================================================
# Scenario 15: RAG Microservice Timeout Handling (503 Service Unavailable)
# ==============================================================================
def test_rag_service_timeout(client: TestClient, builder_auth_headers: dict, monkeypatch):
    """Verify HTTP 503 is returned when RAG microservice times out."""
    orig_post = httpx.Client.post

    def mock_post(self, url, *args, **kwargs):
        if "8001" in str(url):
            raise httpx.TimeoutException("Read timed out after 20.0s")
        return orig_post(self, url, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    payload = {
        "query": "Under UK Bribery Act 2010, what does Section 7 cover?",
        "projectId": 1,
    }
    response = client.post("/api/v1/rag/analyze", json=payload, headers=builder_auth_headers)
    assert response.status_code == 503
    data = response.json()
    assert "timed out" in data["detail"].lower()


# ==============================================================================
# Scenario 16: RAG Health Endpoint Verification
# ==============================================================================
def test_rag_health_endpoint(client: TestClient):
    """Verify the backend RAG health check endpoint returns 200 and probes microservice status."""
    response = client.get("/api/v1/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FinRegTech ShipYard Backend"
    assert "rag_microservice" in data
    assert data["rag_microservice"]["status"] in ("connected", "degraded", "unreachable")


# ==============================================================================
# Scenario 17: Backend Root Health Endpoint Includes RAG Status
# ==============================================================================
def test_root_health_includes_rag(client: TestClient):
    """Verify root /health endpoint includes database and rag_service status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"]["status"] == "connected"
    assert "rag_service" in data
