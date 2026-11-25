"""Tests for Frontend Builder & Main Backend Gateway Integration.

Verifies:
1. POST /api/v1/rag/analyze endpoint availability, schema conformity, and grounded response.
2. Builder payload flexibility (query, prompt, text, question field aliases).
3. Root fallback endpoint POST /rag/analyze.
4. Gateway route POST /api/v1/projects/{projectId}/compare-advice (both Format A 200 and Format B 409).
5. Grounded evidence, citations, provenance, and tenant isolation through /api/v1/rag/analyze.
6. Proper HTTP 422 error handling for invalid/empty requests.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """TestClient for FastAPI app."""
    return TestClient(app)


# ==============================================================================
# 1. POST /api/v1/rag/analyze Endpoint Tests
# ==============================================================================

def test_rag_analyze_standard_query_returns_200(client):
    """Verify POST /api/v1/rag/analyze accepts standard query and returns StructuredAIResponse."""
    payload = {
        "query": "What procedures should commercial organisations implement to prevent bribery?",
        "context": {"jurisdiction": "UK"},
    }
    response = client.post("/api/v1/rag/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["grounded"] is True
    assert data["status"] == "GROUNDED"
    assert len(data["citations"]) > 0
    assert len(data["retrieved_evidence"]) > 0
    assert data["metadata"]["requires_human_review"] is True

    # Verify citation fields
    cit = data["citations"][0]
    assert "source_id" in cit
    assert "regulation" in cit
    assert "section_article" in cit
    assert "jurisdiction" in cit


def test_rag_analyze_builder_prompt_alias_returns_200(client):
    """Verify POST /api/v1/rag/analyze accepts 'prompt' field instead of 'query' for Builder compatibility."""
    payload = {
        "prompt": "What are adequate procedures under the UK Bribery Act?",
        "context": {"jurisdiction": "UK"},
    }
    response = client.post("/api/v1/rag/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert data["query"] == "What are adequate procedures under the UK Bribery Act?"


def test_rag_analyze_builder_text_alias_returns_200(client):
    """Verify POST /api/v1/rag/analyze accepts 'text' field instead of 'query' for Builder compatibility."""
    payload = {
        "text": "What are the criminal penalties for bribing another person under Section 1?",
    }
    response = client.post("/api/v1/rag/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True
    assert "Section 1" in data["query"]


def test_rag_analyze_root_path_returns_200(client):
    """Verify root-level fallback POST /rag/analyze works without /api/v1 prefix."""
    payload = {
        "query": "What are adequate procedures to prevent bribery?",
    }
    response = client.post("/rag/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["grounded"] is True


def test_rag_analyze_validation_empty_query_returns_422(client):
    """Verify empty query to /api/v1/rag/analyze returns HTTP 422."""
    response = client.post("/api/v1/rag/analyze", json={"query": ""})
    assert response.status_code == 422


def test_rag_analyze_validation_whitespace_returns_422(client):
    """Verify whitespace-only query to /api/v1/rag/analyze returns HTTP 422."""
    response = client.post("/api/v1/rag/analyze", json={"query": "   \t\n  "})
    assert response.status_code == 422


# ==============================================================================
# 2. Tenant Isolation & Evidence Classification on /api/v1/rag/analyze
# ==============================================================================

def test_rag_analyze_tenant_isolation(client):
    """Verify /api/v1/rag/analyze scopes strictly by root project_id and context does not leak."""
    payload = {
        "query": "What are adequate procedures to prevent bribery?",
        "context": {"project_id": "PRJ-AUDIT-CONTEXT-ONLY"},
    }
    response = client.post("/api/v1/rag/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    for prov in data.get("provenance", []):
        assert prov.get("project_id") is None


def test_rag_analyze_unapproved_status_preserved(client):
    """Verify candidate records are not falsely represented as approved."""
    payload = {
        "query": "What are adequate procedures to prevent bribery?",
    }
    response = client.post("/api/v1/rag/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["approved_evidence_count"] == 0
    assert data["metadata"]["has_candidate_evidence"] is True
    assert data["metadata"]["requires_human_review"] is True


# ==============================================================================
# 3. Gateway Route POST /api/v1/projects/{projectId}/compare-advice
# ==============================================================================

def test_gateway_route_compare_advice_format_a_returns_200(client):
    """Verify Gateway route /api/v1/projects/{projectId}/compare-advice works with Format A."""
    payload = {
        "advisor_1": {
            "advice_id": "ADV-001",
            "advice_text": "Commercial organisations are strictly liable under Section 7 unless adequate procedures are proven.",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advice_text": "Commercial organisations bear the burden of showing reasonable prevention procedures.",
        },
    }
    response = client.post("/api/v1/projects/PRJ-ABC-999/compare-advice", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] is None
    assert data["human_review_required"] is True
    assert data["traceability"]["project_id"] == "PRJ-ABC-999"


def test_gateway_route_compare_advice_format_b_returns_409(client):
    """Verify Gateway route /api/v1/projects/{projectId}/compare-advice returns 409 for bare IDs."""
    payload = {
        "advisor_1_id": "ADV-001",
        "advisor_2_id": "ADV-002",
    }
    response = client.post("/api/v1/projects/PRJ-ABC-999/compare-advice", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["status"] == "ADVISOR_DATA_NOT_RESOLVED"
    assert data["project_id"] == "PRJ-ABC-999"
    assert data["decision"] is None
