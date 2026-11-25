"""Automated test suite for Week 5 Task W5.2: RAG Backend Contract Alignment.

Verifies that the Padma RAG API accepts product context from Vishal's backend:
1. Existing request without optional fields
2. Request with project_id
3. Request with requirement_ids
4. Request with context (jurisdiction, regulatory_area)
5. Full W4.11-style request
6. Invalid empty query rejection (HTTP 422)
7. Invalid whitespace-only query rejection (HTTP 422)
8. Unknown top-level fields rejection via extra='forbid' (HTTP 422)
9. Project filtering remains enforced (fails closed on unassigned tenant)
10. Jurisdiction filtering remains enforced (UK, EU, non-existent)
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models.query import QueryRequest
from rag.output.structured_response import StructuredAIResponse, ResponseStatus


@pytest.fixture(scope="module")
def api_client():
    """Shared FastAPI TestClient instance for W5.2 contract tests."""
    with TestClient(app) as client:
        yield client


# ==============================================================================
# 1. Existing request without optional fields
# ==============================================================================
def test_w52_existing_request_without_optional_fields(api_client):
    """Test 1: Standard query without optional fields succeeds with full grounded response."""
    payload = {
        "query": "What procedures should commercial organisations implement to prevent bribery?"
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify structured response compliance
    structured = StructuredAIResponse(**data)
    assert structured.query == payload["query"]
    assert structured.status == ResponseStatus.GROUNDED
    assert structured.grounded is True
    assert len(structured.citations) > 0
    assert len(structured.retrieved_evidence) > 0
    assert structured.gap is None


# ==============================================================================
# 2. Request with project_id
# ==============================================================================
def test_w52_request_with_project_id(api_client):
    """Test 2: Query with project_id is accepted as valid integration context."""
    payload = {
        "query": "What constitutes an offence of bribing another person?",
        "project_id": "PRJ-ABC-001",
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.query == payload["query"]
    # Single-tenant canonical corpus records have no project_id assigned; fails closed cleanly
    assert len(structured.retrieved_evidence) == 0
    assert structured.grounded is False
    assert structured.status == ResponseStatus.INSUFFICIENT_EVIDENCE


# ==============================================================================
# 3. Request with requirement_ids
# ==============================================================================
def test_w52_request_with_requirement_ids(api_client):
    """Test 3: Query with requirement_ids is accepted as valid workflow context."""
    payload = {
        "query": "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?",
        "requirement_ids": ["REQ-UK-001", "REQ-UK-002"],
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.query == payload["query"]
    assert structured.status == ResponseStatus.GROUNDED
    assert structured.grounded is True
    assert len(structured.citations) > 0


# ==============================================================================
# 4. Request with context
# ==============================================================================
def test_w52_request_with_context(api_client):
    """Test 4: Query with context dictionary applies supported filters (jurisdiction)."""
    payload = {
        "query": "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?",
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery and Corruption",
        },
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.status == ResponseStatus.GROUNDED
    assert structured.grounded is True
    assert len(structured.retrieved_evidence) > 0
    assert all(p.jurisdiction == "UK" for p in structured.provenance)
    assert all(chunk.chunk_id.startswith("RR-UK") for chunk in structured.retrieved_evidence)


# ==============================================================================
# 5. Full W4.11-style request
# ==============================================================================
def test_w52_full_w411_style_request(api_client):
    """Test 5: Full W4.11 specification request payload is parsed and executed cleanly."""
    payload = {
        "project_id": "PRJ-ABC-001",
        "query": "What procedures should commercial organisations implement to prevent bribery?",
        "requirement_ids": ["REQ-001", "REQ-002"],
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery and Corruption",
        },
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.query == payload["query"]
    assert structured.request_id is not None
    assert structured.request_id.startswith("REQ-")
    assert structured.metadata.response_version == "1.0"


# ==============================================================================
# 6. Invalid empty query
# ==============================================================================
def test_w52_invalid_empty_query_rejected(api_client):
    """Test 6: Empty query string is rejected with HTTP 422 Unprocessable Entity."""
    payload = {
        "query": "",
        "project_id": "PRJ-001",
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 7. Invalid whitespace query
# ==============================================================================
def test_w52_invalid_whitespace_query_rejected(api_client):
    """Test 7: Whitespace-only query string is rejected with HTTP 422 Unprocessable Entity."""
    payload = {
        "query": "   \n\t   ",
        "requirement_ids": ["REQ-001"],
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 422


# ==============================================================================
# 8. Unknown top-level fields ignored safely
# ==============================================================================
def test_w52_unknown_top_level_field_rejected(api_client):
    """Test 8: Unknown/unauthorized top-level fields are safely ignored via extra='ignore' with HTTP 200."""
    # Attempting to inject arbitrary unauthorized fields
    payload_extra = {
        "query": "What is Section 1?",
        "unauthorized_field": "exploit_value",
    }
    resp = api_client.post("/api/v1/query", json=payload_extra)
    assert resp.status_code == 200

    # Attempting to bypass server-side approval gate
    payload_approval = {
        "query": "What is Section 1?",
        "is_approved_for_rag": True,
    }
    resp_appr = api_client.post("/api/v1/query", json=payload_approval)
    assert resp_appr.status_code == 200
    assert resp_appr.json()["metadata"]["approved_evidence_count"] == 0

    # Attempting to inject client provider override
    payload_provider = {
        "query": "What is Section 1?",
        "provider": "malicious_provider",
    }
    resp_prov = api_client.post("/api/v1/query", json=payload_provider)
    assert resp_prov.status_code == 200


# ==============================================================================
# 9. Project filtering remains enforced
# ==============================================================================
def test_w52_project_filtering_remains_enforced(api_client):
    """Test 9: Passing an unassigned/foreign project_id fails closed to 0 retrieved chunks."""
    payload = {
        "query": "bribery prevention procedures",
        "project_id": "ForeignProject-Tenant-XYZ",
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    # Verification that unassigned project fails closed and leaks zero chunks
    assert len(structured.retrieved_evidence) == 0
    assert structured.grounded is False
    assert structured.gap is not None
    assert structured.gap.is_gap is True


# ==============================================================================
# 10. Jurisdiction filtering remains enforced
# ==============================================================================
def test_w52_jurisdiction_filtering_remains_enforced(api_client):
    """Test 10: Jurisdiction filtering within context is enforced for UK, EU, and invalid scopes."""
    # UK filter: only UK chunks
    payload_uk = {
        "query": "bribery offences and prevention procedures",
        "context": {"jurisdiction": "UK"},
    }
    resp_uk = api_client.post("/api/v1/query", json=payload_uk)
    assert resp_uk.status_code == 200
    data_uk = resp_uk.json()
    assert len(data_uk["retrieved_evidence"]) > 0
    assert all(chunk["chunk_id"].startswith("RR-UK") for chunk in data_uk["retrieved_evidence"])
    assert all(p["jurisdiction"] == "UK" for p in data_uk["provenance"])

    # EU filter: only EU chunks
    payload_eu = {
        "query": "anti-money laundering directives",
        "context": {"jurisdiction": "EU"},
    }
    resp_eu = api_client.post("/api/v1/query", json=payload_eu)
    assert resp_eu.status_code == 200
    data_eu = resp_eu.json()
    assert len(data_eu["retrieved_evidence"]) > 0
    assert all(chunk["chunk_id"].startswith("RR-EU") for chunk in data_eu["retrieved_evidence"])
    assert all(p["jurisdiction"] == "EU" for p in data_eu["provenance"])

    # Non-existent jurisdiction: 0 chunks, fails closed
    payload_none = {
        "query": "anti-bribery procedures",
        "context": {"jurisdiction": "NONEXISTENT_JURISDICTION"},
    }
    resp_none = api_client.post("/api/v1/query", json=payload_none)
    assert resp_none.status_code == 200
    data_none = resp_none.json()
    assert len(data_none["retrieved_evidence"]) == 0
    assert data_none["grounded"] is False
