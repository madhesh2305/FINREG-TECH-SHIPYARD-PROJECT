"""Automated test suite for Week 5 Task W5.3: RAG Frontend Integration Support.

Verifies the RAG API output contract, serialization fidelity, status mapping,
and security constraints for Harshini's frontend and Vishal's backend:
1. SUCCESS response serializes correctly
2. CONFLICT_DETECTED response serializes correctly
3. GAP_DETECTED response serializes correctly
4. NO_SOURCE_FOUND response serializes correctly
5. ERROR response serializes correctly
6. Citations and provenance remain serializable
7. Response schema remains backward compatible
8. Full W4.11 request remains accepted with custom id
9. No unsupported frontend-only fields silently added to schema
"""

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_grounded_generator
from api.models.query import QueryRequest
from rag.retrieval.retriever import RetrievalResult
from rag.output.structured_response import (
    StructuredAIResponse,
    ResponseStatus,
    RetrievedEvidenceItem,
    ResponseMetadata,
)
from rag.generation.grounded_generator import GroundedGenerator, GroundedResponse
from rag.generation.citations import Citation, ProvenanceRecord
from rag.generation.gap_handler import GapResult, GapType
from rag.conflict.conflict_detector import ConflictFinding, ConflictType


@pytest.fixture(scope="module")
def api_client():
    """Shared FastAPI TestClient instance for W5.3 contract tests."""
    with TestClient(app) as client:
        yield client


# ==============================================================================
# 1. SUCCESS response serializes correctly
# ==============================================================================
def test_w53_success_response_serializes_correctly(api_client):
    """Test 1: SUCCESS response serializes to JSON cleanly with answer, citations, and grounded=True."""
    mock_gen = GroundedGenerator()
    c1 = RetrievalResult(
        chunk_id="RR-UK-01-C01",
        record_id="RR-UK-01",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Offences of bribing another person",
        text="Offences of bribing another person text content",
        text_type="retrieval_text",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.75,
        distance=0.25,
    )
    citation = Citation.from_retrieval_result(c1)
    provenance = ProvenanceRecord(
        chunk_id="RR-UK-01-C01",
        record_id="RR-UK-01",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        section_article="Section 1",
        title="Offences of bribing another person",
        jurisdiction="UK",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        text_type="retrieval_text",
        similarity_score=0.75,
    )
    grounded_resp = GroundedResponse(
        query="What constitutes an offence of bribing another person?",
        answer="Under Section 1, bribing another person is an offence [Bribery Act 2010, Section 1].",
        evidence_used=["RR-UK-01-C01"],
        confidence_status="GROUNDED",
        grounded=True,
        evidence_count=1,
        citations=[citation],
        provenance=[provenance],
        conflicts=[],
        gap=None,
    )
    structured_resp = grounded_resp.to_structured_response(retrieved_chunks=[c1], request_id="REQ-TEST-SUCCESS")

    with patch.object(mock_gen, "generate_structured_response", return_value=structured_resp):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            resp = api_client.post("/api/v1/query", json={"query": "What constitutes an offence of bribing another person?"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "GROUNDED"
            assert structured_resp.to_external_status() == "SUCCESS"
            assert data["grounded"] is True
            assert len(data["citations"]) == 1
            assert len(data["provenance"]) == 1
            assert data["gap"] is None
            # Verify clean JSON serialization
            serialized = json.dumps(data)
            assert "RR-UK-01-C01" in serialized
        finally:
            app.dependency_overrides.clear()


# ==============================================================================
# 2. CONFLICT_DETECTED response serializes correctly
# ==============================================================================
def test_w53_conflict_detected_response_serializes_correctly(api_client):
    """Test 2: CONFLICT_DETECTED response serializes with documented relationships and review flag."""
    payload = {
        "query": "How do the UK Bribery Act 2010 statutory offences relate to the Ministry of Justice Six Principles guidance?",
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.to_external_status() == "CONFLICT_DETECTED"
    assert len(structured.conflicts) > 0
    assert structured.metadata.requires_human_review is True
    assert structured.conflicts[0].both_sources_retrieved is True

    # JSON serialization integrity
    json_str = structured.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["conflicts"][0]["conflict_id"].startswith("CO-")
    assert parsed["metadata"]["conflict_count"] > 0


# ==============================================================================
# 3. GAP_DETECTED response serializes correctly
# ==============================================================================
def test_w53_gap_detected_response_serializes_correctly(api_client):
    """Test 3: GAP_DETECTED response serializes with structured gap and empty citations."""
    payload = {
        "query": "What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?",
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.to_external_status() == "GAP_DETECTED"
    assert structured.grounded is False
    assert structured.gap is not None
    assert structured.gap.is_gap is True
    assert structured.gap.coverage_nature == "CORPUS_COVERAGE_LIMITATION"
    assert structured.citations == []
    assert structured.provenance == []

    # JSON serialization integrity
    json_str = structured.model_dump_json()
    assert "user_safe_message" in json_str


# ==============================================================================
# 4. NO_SOURCE_FOUND response serializes correctly
# ==============================================================================
def test_w53_no_source_found_response_serializes_correctly(api_client):
    """Test 4: NO_SOURCE_FOUND response serializes policy notice without hallucinations."""
    mock_gen = GroundedGenerator()
    gap_res = GapResult(
        is_gap=True,
        gap_type=GapType.UNAPPROVED_EVIDENCE,
        message="All records are unapproved Candidate records.",
        user_safe_message="No approved authoritative regulatory records were found.",
        requires_human_review=True,
        coverage_nature="UNAPPROVED_EVIDENCE",
    )
    grounded_resp = GroundedResponse(
        query="Explain bribery offences",
        answer="No approved sources found.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap_res,
        citations=[],
        provenance=[],
        conflicts=[],
    )
    structured_resp = grounded_resp.to_structured_response(retrieved_chunks=[], request_id="REQ-NO-SOURCE")

    with patch.object(mock_gen, "generate_structured_response", return_value=structured_resp):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            resp = api_client.post("/api/v1/query", json={"query": "Explain bribery offences"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "UNAPPROVED_EVIDENCE"
            assert structured_resp.to_external_status() == "NO_SOURCE_FOUND"
            assert data["grounded"] is False
            assert len(data["retrieved_evidence"]) == 0
            assert len(data["citations"]) == 0
        finally:
            app.dependency_overrides.clear()


# ==============================================================================
# 5. ERROR response serializes correctly
# ==============================================================================
def test_w53_error_response_serializes_correctly(api_client):
    """Test 5: Technical errors serialize to safe HTTP 500 without internal leaks."""
    mock_gen = GroundedGenerator()
    with patch.object(mock_gen, "generate_structured_response", side_effect=RuntimeError("Internal database down at /var/db")):
        app.dependency_overrides[get_grounded_generator] = lambda: mock_gen
        try:
            resp = api_client.post("/api/v1/query", json={"query": "Valid regulatory question"})
            assert resp.status_code == 500
            data = resp.json()
            assert "detail" in data
            assert data["detail"] == "An internal server error occurred while processing the regulatory query."
            # Stack trace and paths never leaked
            assert "RuntimeError" not in resp.text
            assert "/var/db" not in resp.text
        finally:
            app.dependency_overrides.clear()

    # Also verify ResponseStatus.ERROR maps to "ERROR"
    err_resp = StructuredAIResponse(query="test", status=ResponseStatus.ERROR, grounded=False)
    assert err_resp.to_external_status() == "ERROR"


# ==============================================================================
# 6. Citations and provenance remain serializable
# ==============================================================================
def test_w53_citations_provenance_remain_serializable(api_client):
    """Test 6: Citations and provenance models round-trip through JSON cleanly."""
    payload = {
        "query": "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?",
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Citations validation
    assert len(data["citations"]) > 0
    cit = data["citations"][0]
    assert "chunk_id" in cit
    assert "record_id" in cit
    assert "source_id" in cit
    assert "citation_id" in cit
    assert "formatted_citation" in cit
    assert "is_approved_for_rag" in cit
    assert "validation_status" in cit

    # Provenance validation
    assert len(data["provenance"]) > 0
    prov = data["provenance"][0]
    assert "regulation" in prov
    assert "section_article" in prov
    assert "jurisdiction" in prov
    assert "official_source" in prov
    assert "effective_date" in prov

    # Full JSON round-trip
    dumped = json.dumps(data)
    reloaded = json.loads(dumped)
    assert reloaded["citations"] == data["citations"]
    assert reloaded["provenance"] == data["provenance"]


# ==============================================================================
# 7. Response schema remains backward compatible
# ==============================================================================
def test_w53_response_schema_remains_backward_compatible():
    """Test 7: StructuredAIResponse constructs with minimal mandatory fields and safe defaults."""
    minimal = StructuredAIResponse(
        query="Minimal compliance question",
        status=ResponseStatus.GROUNDED,
        grounded=True,
    )
    assert minimal.request_id is None
    assert minimal.answer is None
    assert minimal.gap is None
    assert minimal.citations == []
    assert minimal.provenance == []
    assert minimal.conflicts == []
    assert minimal.retrieved_evidence == []
    assert minimal.metadata.response_version == "1.0"
    assert minimal.metadata.retrieved_count == 0


# ==============================================================================
# 8. Full W4.11 request remains accepted with custom id
# ==============================================================================
def test_w53_w411_request_remains_accepted(api_client):
    """Test 8: Full representative W4.11 request is parsed and echoes custom id as request_id."""
    payload = {
        "id": "n1ggk9",
        "project_id": "PRJ-ABC-001",
        "query": "What regulatory requirements apply to our anti-bribery controls?",
        "requirement_ids": ["REQ-001", "REQ-002"],
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery",
        },
    }
    response = api_client.post("/api/v1/query", json=payload)
    assert response.status_code == 200
    data = response.json()

    structured = StructuredAIResponse(**data)
    assert structured.request_id == "n1ggk9"
    assert structured.query == payload["query"]
    assert structured.metadata.response_version == "1.0"


# ==============================================================================
# 9. No unsupported frontend-only fields silently added to schema
# ==============================================================================
def test_w53_no_unsupported_frontend_fields_added():
    """Test 9: Exact canonical 11 fields on StructuredAIResponse; no unauthorized fields added."""
    expected_fields = {
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
    actual_fields = set(StructuredAIResponse.model_fields.keys())
    assert actual_fields == expected_fields, f"Unexpected fields added: {actual_fields - expected_fields}"

    # Verify QueryRequest strictly forbids client extra fields
    with pytest.raises(Exception):
        QueryRequest(
            query="test query",
            unsupported_ui_state="draft",  # type: ignore
        )
