"""Automated test suite for Task 11 FastAPI backend integration.

Verifies health endpoints, query validation, response schema compliance,
error handling, security gating, and OpenAPI contract specification.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from api.main import app
from api.dependencies import get_grounded_generator
from rag.output.structured_response import StructuredAIResponse, ResponseStatus
from rag.generation.grounded_generator import GroundedGenerator, GroundedResponse
from rag.generation.gap_handler import GapResult, GapType


@pytest.fixture(scope="module")
def client():
    """Shared FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# 1. Health Endpoints Tests
# ---------------------------------------------------------------------------

def test_health_endpoint_root_returns_200(client):
    """Test 1: Root GET /health endpoint returns 200 with non-sensitive status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "ABC Shield FinRegTech API"
    assert data["version"] == "1.0.0"
    assert data["rag_pipeline_initialized"] is True
    assert data["chromadb_status"] == "connected"
    # Ensure no sensitive filesystem paths or credentials leaked
    assert "data/processed" not in str(data)
    assert "path" not in data


def test_health_endpoint_v1_returns_200(client):
    """Test 2: Versioned GET /api/v1/health returns 200 with identical status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["chromadb_status"] == "connected"


# ---------------------------------------------------------------------------
# 2. Query Endpoint Happy Paths & Schema Tests
# ---------------------------------------------------------------------------

def test_valid_query_returns_200(client):
    """Test 3: Valid query returns HTTP 200."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What procedures should commercial organisations implement to prevent bribery?"},
    )
    assert response.status_code == 200


def test_response_matches_structured_ai_response_schema(client):
    """Test 4: Response adheres strictly to Task 9 StructuredAIResponse schema."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What procedures should commercial organisations implement to prevent bribery?"},
    )
    assert response.status_code == 200
    data = response.json()
    # Validate by parsing into Pydantic model
    structured_obj = StructuredAIResponse(**data)
    assert structured_obj.query == "What procedures should commercial organisations implement to prevent bribery?"
    assert structured_obj.status in [s for s in ResponseStatus]
    assert isinstance(structured_obj.citations, list)
    assert isinstance(structured_obj.provenance, list)
    assert isinstance(structured_obj.conflicts, list)
    assert isinstance(structured_obj.retrieved_evidence, list)
    assert structured_obj.metadata.response_version == "1.0"


def test_request_id_exists_and_formatted(client):
    """Test 5: Response contains a unique, server-generated request_id formatted as REQ-<uuid>."""
    response = client.post(
        "/api/v1/query",
        json={"query": "Explain Section 1 of the Bribery Act 2010."},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["request_id"] is not None
    assert data["request_id"].startswith("REQ-")
    assert len(data["request_id"]) > 10


def test_query_is_preserved_in_response(client):
    """Test 6: The original query text is preserved in the response."""
    test_q = "Explain Section 1 of the Bribery Act 2010."
    response = client.post("/api/v1/query", json={"query": test_q})
    assert response.status_code == 200
    assert response.json()["query"] == test_q


def test_grounded_response_passes_through_correctly(client):
    """Test 7: Grounded answers correctly pass through with citations and evidence."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "GROUNDED"
    assert data["grounded"] is True
    assert len(data["citations"]) > 0
    assert len(data["provenance"]) > 0
    assert len(data["retrieved_evidence"]) > 0
    assert data["gap"] is None


def test_insufficient_evidence_passes_through_correctly(client):
    """Test 8: Missing provision returns HTTP 200 with INSUFFICIENT_EVIDENCE status (not HTTP error)."""
    mock_gen = GroundedGenerator()
    gap_res = GapResult(
        is_gap=True,
        gap_type=GapType.MISSING_SPECIFIC_PROVISION,
        message="Specific provision not found in corpus",
        user_safe_message="The requested specific provision could not be found in the regulatory evidence.",
    )
    grounded_resp = GroundedResponse(
        query="What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?",
        answer="I do not have sufficient evidence.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap_res,
    )
    mock_structured = grounded_resp.to_structured_response(retrieved_chunks=[])

    with patch.object(mock_gen, "generate_structured_response", return_value=mock_structured):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            response = client.post(
                "/api/v1/query",
                json={"query": "What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "INSUFFICIENT_EVIDENCE"
            assert data["grounded"] is False
            assert data["gap"] is not None
            assert data["gap"]["is_gap"] is True
            assert data["gap"]["gap_type"] == "MISSING_SPECIFIC_PROVISION"
        finally:
            app.dependency_overrides.clear()


def test_out_of_scope_passes_through_correctly(client):
    """Test 9: Out-of-scope domain returns HTTP 200 with OUT_OF_SCOPE status."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What cybersecurity requirements apply to financial entities?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OUT_OF_SCOPE"
    assert data["grounded"] is False
    assert data["gap"] is not None
    assert data["gap"]["gap_type"] == "OUT_OF_SCOPE"


def test_unapproved_evidence_status_preserved(client):
    """Test 10: UNAPPROVED_EVIDENCE status correctly passes through when evidence is unapproved."""
    # Mock generator returning an UNAPPROVED_EVIDENCE response
    mock_gen = GroundedGenerator()
    gap_res = GapResult(
        is_gap=True,
        gap_type=GapType.UNAPPROVED_EVIDENCE,
        message="Gated candidate evidence",
        user_safe_message="Records are unapproved",
    )
    grounded_resp = GroundedResponse(
        query="Mock unapproved query",
        answer="Evidence is candidate only.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap_res,
    )
    mock_structured = grounded_resp.to_structured_response(retrieved_chunks=[])

    with patch.object(mock_gen, "generate_structured_response", return_value=mock_structured):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            response = client.post("/api/v1/query", json={"query": "Mock unapproved query"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "UNAPPROVED_EVIDENCE"
            assert data["grounded"] is False
            assert data["gap"]["gap_type"] == "UNAPPROVED_EVIDENCE"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 3. Input Validation Tests (HTTP 422)
# ---------------------------------------------------------------------------

def test_empty_query_rejected_422(client):
    """Test 11: Empty query is rejected with HTTP 422."""
    response = client.post("/api/v1/query", json={"query": ""})
    assert response.status_code == 422


def test_whitespace_only_query_rejected_422(client):
    """Test 12: Whitespace-only query is rejected with HTTP 422."""
    response = client.post("/api/v1/query", json={"query": "    \t \n   "})
    assert response.status_code == 422


def test_oversized_query_rejected_422(client):
    """Test 13: Oversized query exceeding configured maximum length is rejected with HTTP 422."""
    oversized_q = "bribery " * 400  # > 2800 chars
    response = client.post("/api/v1/query", json={"query": oversized_q})
    assert response.status_code == 422


def test_client_cannot_modify_approval_status(client):
    """Test 14: Client cannot submit or modify server-controlled regulatory metadata."""
    payload = {
        "query": "What is Section 1?",
        "is_approved_for_rag": True,
        "validation_status": "Approved",
    }
    response = client.post("/api/v1/query", json=payload)
    # Pydantic extra='forbid' rejects client attempt to inject regulatory metadata
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. Server-Generated Security Guarantees
# ---------------------------------------------------------------------------

def test_citations_remain_server_generated(client):
    """Test 15: Citations in response strictly derive from retrieved chunks."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What procedures should commercial organisations implement to prevent bribery?"},
    )
    assert response.status_code == 200
    data = response.json()
    retrieved_chunk_ids = {e["chunk_id"] for e in data["retrieved_evidence"]}
    for citation in data["citations"]:
        assert citation["chunk_id"] in retrieved_chunk_ids


def test_conflicts_remain_server_generated(client):
    """Test 16: Documented conflicts in response map strictly to controlled CO-xxx register."""
    response = client.post(
        "/api/v1/query",
        json={"query": "How do the UK Bribery Act 2010 statutory offences relate to the Ministry of Justice Six Principles guidance?"},
    )
    assert response.status_code == 200
    data = response.json()
    for conf in data["conflicts"]:
        assert conf["conflict_id"].startswith("CO-")


def test_gap_remains_server_generated(client):
    """Test 17: GAP structure is strictly server-generated when present."""
    response = client.post(
        "/api/v1/query",
        json={"query": "What cybersecurity requirements apply to financial entities?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["gap"] is not None
    assert "gap_type" in data["gap"]
    assert "user_safe_message" in data["gap"]


# ---------------------------------------------------------------------------
# 5. Error Handling & Safety Tests (HTTP 500)
# ---------------------------------------------------------------------------

def test_internal_errors_converted_to_safe_500(client):
    """Test 18: Unexpected pipeline exceptions return HTTP 500 with generic error message."""
    mock_gen = GroundedGenerator()
    with patch.object(mock_gen, "generate_structured_response", side_effect=RuntimeError("Secret internal database error at /var/secrets/key")):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            response = client.post("/api/v1/query", json={"query": "Valid test question"})
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert data["detail"] == "An internal server error occurred while processing the regulatory query."
        finally:
            app.dependency_overrides.clear()


def test_no_stack_trace_returned_on_500(client):
    """Test 19: No stack trace, file path, or exception internals leaked on HTTP 500."""
    mock_gen = GroundedGenerator()
    with patch.object(mock_gen, "generate_structured_response", side_effect=ValueError("Internal sensitive detail")):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            response = client.post("/api/v1/query", json={"query": "Valid test question"})
            assert response.status_code == 500
            body = response.text
            assert "Traceback" not in body
            assert "File " not in body
            assert "line " not in body
            assert "Internal sensitive detail" not in body
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 6. OpenAPI Contract Specification Test
# ---------------------------------------------------------------------------

def test_openapi_schema_matches_contract(client):
    """Test 20: /openapi.json exposes expected metadata, schemas, and endpoints."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "ABC Shield FinRegTech API"
    assert schema["info"]["version"] == "1.0.0"
    paths = schema["paths"]
    assert "/health" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/query" in paths
    assert "post" in paths["/api/v1/query"]
    # Verify StructuredAIResponse is defined in components
    components = schema["components"]["schemas"]
    assert "StructuredAIResponse" in components
    assert "QueryRequest" in components
    assert "ResponseStatus" in components
