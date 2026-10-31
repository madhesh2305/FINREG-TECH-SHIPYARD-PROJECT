"""Tests for the newly routed AI/RAG endpoints under /api/v1 per Padma's handover specification:
1. GET /api/v1/health
2. POST /api/v1/query
3. POST /api/v1/compare
4. CORS Origin, Methods, Headers, and Credentials
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_rag_health_handover_spec():
    """Verify GET /api/v1/health returns { status: 'ok', service: 'finreg-rag-engine' }."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "finreg-rag-engine"
    assert "details" in data


def test_rag_query_public_corpus():
    """Verify POST /api/v1/query with project_id: null queries general public regulatory corpus."""
    payload = {
        "project_id": None,
        "query": "What are the CDD verification timelines under MLR 2017?",
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    # Required response keys per spec
    assert "request_id" in data
    assert "query" in data
    assert data["query"] == payload["query"]
    assert "status" in data
    assert "grounded" in data
    assert "answer" in data
    assert "gap" in data
    assert "citations" in data
    assert "provenance" in data
    assert "conflicts" in data
    assert "retrieved_evidence" in data
    assert "metadata" in data

    # Metadata requirements
    meta = data["metadata"]
    assert "retrieved_count" in meta
    assert "approved_evidence_count" in meta
    assert "citation_count" in meta
    assert "conflict_count" in meta
    assert "requires_human_review" in meta

    # Approval flags (boolean)
    for c in data["citations"]:
        assert isinstance(c.get("is_approved_for_rag"), bool)
    for ev in data["retrieved_evidence"]:
        assert isinstance(ev.get("is_approved_for_rag"), bool)
    for p in data["provenance"]:
        assert isinstance(p.get("is_approved_for_rag"), bool)

    # Complementary regulations labeled as OVERLAP
    for conf in data["conflicts"]:
        assert conf.get("conflict_type") == "OVERLAP"


def test_rag_query_tenant_isolation():
    """Verify POST /api/v1/query with project_id scopes retrieval strictly to tenant evidence."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "query": "What are the CDD verification timelines under MLR 2017?",
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Tenant has no private policy uploads, returns INSUFFICIENT_EVIDENCE
    assert data["status"] in ("INSUFFICIENT_EVIDENCE", "TENANT_SCOPE_NO_EVIDENCE")
    assert data["grounded"] is False
    assert data.get("gap") is not None
    assert len(data.get("citations", [])) == 0


def test_rag_compare_handover_spec():
    """Verify POST /api/v1/compare matches Padma's non-adjudication handover specification."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "advisor_1_id": "ADV-101",
        "advisor_2_id": "ADV-102",
        "topic": "Timing of Customer Due Diligence Verification",
    }
    response = client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()

    # Exact required fields
    assert "comparison_id" in data
    assert "advisor_1" in data
    assert "advisor_2" in data
    assert "differences" in data
    assert "relationships" in data
    assert "supporting_evidence" in data
    assert "citations" in data
    assert "provenance" in data
    assert "evidence_gaps" in data
    assert "human_review_required" in data
    assert "decision" in data
    assert "disclaimer" in data
    assert "traceability" in data

    # Non-adjudication invariants
    assert data["human_review_required"] is True
    assert data["decision"] is None

    # Relationship Types & Approval Flags
    for r in data["relationships"]:
        assert r.get("conflict_type") == "OVERLAP"
        assert isinstance(r.get("is_approved_for_rag"), bool)

    for c in data["citations"]:
        assert isinstance(c.get("is_approved_for_rag"), bool)

    for p in data["provenance"]:
        assert isinstance(p.get("is_approved_for_rag"), bool)


def test_cors_configuration_handover_spec():
    """Verify CORS configuration allows origin http://localhost:5173 with credentials and required methods."""
    # Preflight OPTIONS check
    res = client.options(
        "/api/v1/query",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res.headers.get("access-control-allow-credentials") == "true"
    allowed_methods = res.headers.get("access-control-allow-methods", "")
    for m in ["GET", "POST", "PATCH", "OPTIONS"]:
        assert m in allowed_methods

    # GET /api/v1/health with Origin header
    res_health = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    assert res_health.status_code == 200
    assert res_health.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res_health.headers.get("access-control-allow-credentials") == "true"
