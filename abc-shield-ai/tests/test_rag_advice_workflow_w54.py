"""Automated test suite for Week 5 — Task W5.4: RAG Inside Advice Workflow.

Verifies the RAG-side Advice integration adapter, correlation traceability,
W4.11 status mapping, advice workflow statuses, citations, provenance,
conflict detection, evidence-gap handling, security fail-closed gating,
and non-adjudication guardrails.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app
from api.models.query import QueryRequest
from rag.pipeline.advice_adapter import (
    AdviceRAGAdapter,
    AdviceRAGResult,
    AdviceWorkflowStatus,
    AdviceTraceabilityContext,
)
from rag.output.structured_response import ResponseStatus, StructuredAIResponse
from rag.generation.grounded_generator import GroundedGenerator


@pytest.fixture(scope="module")
def api_client():
    """Shared TestClient instance for API route integration verification."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def advice_adapter():
    """Shared AdviceRAGAdapter instance."""
    return AdviceRAGAdapter()


# ==============================================================================
# 1. Advice context creates a valid RAG request
# ==============================================================================
def test_w54_advice_context_creates_valid_rag_request(advice_adapter):
    """Test 1: Advice context (id, requirement_ids, advisor_advice_ids, context) executes cleanly and grounds response."""
    request = QueryRequest(
        id="ADV-REQ-001",
        query="What procedures should commercial organisations implement to prevent bribery?",
        requirement_ids=["REQ-001", "REQ-002"],
        advisor_advice_ids=["ADV-UK-001"],
        context={
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery and Corruption",
        },
    )

    result = advice_adapter.execute_from_request(request)

    assert isinstance(result, AdviceRAGResult)
    assert result.response.status == ResponseStatus.GROUNDED
    assert result.external_status in ["SUCCESS", "CONFLICT_DETECTED"]
    assert result.workflow_status in [AdviceWorkflowStatus.RAG_SUPPORTED, AdviceWorkflowStatus.RAG_REVIEW_REQUIRED]
    assert result.traceability.request_id == "ADV-REQ-001"
    assert result.traceability.requirement_ids == ["REQ-001", "REQ-002"]
    assert result.traceability.advisor_advice_ids == ["ADV-UK-001"]
    assert result.traceability.jurisdiction == "UK"
    assert result.traceability.regulatory_area == "Anti-Bribery and Corruption"



# ==============================================================================
# 2. project_id is passed as context correctly
# ==============================================================================
def test_w54_project_id_passed_as_context_correctly(advice_adapter):
    """Test 2: project_id is propagated to retriever context and preserved in traceability."""
    result = advice_adapter.execute_advice_rag(
        query="What is an offence under the Bribery Act 2010?",
        project_id="PRJ-TENANT-X",
    )
    assert result.traceability.project_id == "PRJ-TENANT-X"
    # Even if unassigned tenant fails closed or executes, project_id is strictly recorded
    assert result.traceability.request_id is not None


# ==============================================================================
# 3. requirement_ids are preserved correctly
# ==============================================================================
def test_w54_requirement_ids_preserved_correctly(advice_adapter):
    """Test 3: requirement_ids are captured in traceability context without mutation."""
    req_ids = ["REQ-101", "REQ-102", "REQ-103"]
    result = advice_adapter.execute_advice_rag(
        query="What constitutes bribery under Section 1?",
        requirement_ids=req_ids,
    )
    assert result.traceability.requirement_ids == req_ids


# ==============================================================================
# 4. jurisdiction / regulatory_area context is preserved where supported
# ==============================================================================
def test_w54_jurisdiction_and_regulatory_area_context_preserved(advice_adapter):
    """Test 4: Context hints (jurisdiction, regulatory_area) are parsed and recorded in traceability."""
    result = advice_adapter.execute_advice_rag(
        query="What are the Ministry of Justice principles?",
        context={"jurisdiction": "UK", "regulatory_area": "Procedures"},
    )
    assert result.traceability.jurisdiction == "UK"
    assert result.traceability.regulatory_area == "Procedures"


# ==============================================================================
# 5. Advice query text reaches the existing RAG pipeline
# ==============================================================================
def test_w54_advice_query_text_reaches_pipeline(advice_adapter):
    """Test 5: The query text reaches the generator and is preserved verbatim in response."""
    test_query = "What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?"
    result = advice_adapter.execute_advice_rag(query=test_query)
    assert result.response.query == test_query


# ==============================================================================
# 6. SUCCESS response is returned correctly
# ==============================================================================
def test_w54_success_response_returned_correctly(advice_adapter):
    """Test 6: Single-source grounded query returns external SUCCESS and workflow RAG_SUPPORTED."""
    result = advice_adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person under Section 1 of the Bribery Act 2010?",
        top_k=1,
    )
    assert result.response.status == ResponseStatus.GROUNDED
    assert result.response.grounded is True
    assert result.external_status == "SUCCESS"
    assert result.workflow_status == AdviceWorkflowStatus.RAG_SUPPORTED
    assert len(result.citations) >= 1
    assert len(result.conflicts) == 0


# ==============================================================================
# 7. CONFLICT_DETECTED response is returned correctly
# ==============================================================================
def test_w54_conflict_detected_response_returned_correctly(advice_adapter):
    """Test 7: Co-retrieved documented relationships return CONFLICT_DETECTED and RAG_REVIEW_REQUIRED."""
    result = advice_adapter.execute_advice_rag(
        query="How do the UK Bribery Act 2010 statutory offences relate to the Ministry of Justice Six Principles guidance?",
    )
    assert result.external_status == "CONFLICT_DETECTED"
    assert result.workflow_status == AdviceWorkflowStatus.RAG_REVIEW_REQUIRED
    assert result.requires_human_review is True
    assert len(result.conflicts) > 0
    assert result.conflicts[0].both_sources_retrieved is True


# ==============================================================================
# 8. GAP_DETECTED response is returned correctly
# ==============================================================================
def test_w54_gap_detected_response_returned_correctly(advice_adapter):
    """Test 8: Query for absent provision returns GAP_DETECTED, RAG_GAP_DETECTED, and 0 citations."""
    result = advice_adapter.execute_advice_rag(
        query="What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?",
    )
    assert result.response.status == ResponseStatus.INSUFFICIENT_EVIDENCE
    assert result.response.grounded is False
    assert result.external_status == "GAP_DETECTED"
    assert result.workflow_status == AdviceWorkflowStatus.RAG_GAP_DETECTED
    assert result.citations == []
    assert result.provenance == []
    assert result.gap is not None
    assert result.gap.is_gap is True


# ==============================================================================
# 9. NO_SOURCE_FOUND behavior remains safe
# ==============================================================================
def test_w54_no_source_found_remains_safe(advice_adapter):
    """Test 9: Approved-only query against candidate corpus returns NO_SOURCE_FOUND with 0 citations."""
    result = advice_adapter.execute_advice_rag(
        query="What procedures should commercial organisations implement to prevent bribery?",
        filter_approved_only=True,
    )
    assert result.response.status == ResponseStatus.UNAPPROVED_EVIDENCE
    assert result.response.grounded is False
    assert result.external_status == "NO_SOURCE_FOUND"
    assert result.workflow_status == AdviceWorkflowStatus.RAG_NO_SOURCES
    assert result.citations == []
    assert result.provenance == []
    assert result.gap.gap_type.value == "UNAPPROVED_EVIDENCE"


# ==============================================================================
# 10. RAG errors are represented correctly
# ==============================================================================
def test_w54_rag_errors_represented_correctly():
    """Test 10: System failures map to external ERROR and workflow RAG_ERROR without leaking secrets."""
    mock_gen = GroundedGenerator()
    adapter = AdviceRAGAdapter(generator=mock_gen)

    with patch.object(mock_gen, "generate_structured_response", side_effect=RuntimeError("Secret DB /var/db/pw failed")):
        # Mode A: with raise_exceptions=False, returns safe ERROR result
        result = adapter.execute_advice_rag(
            query="What is bribery?",
            request_id="ERR-REQ-123",
            raise_exceptions=False,
        )
        assert result.external_status == "ERROR"
        assert result.workflow_status == AdviceWorkflowStatus.RAG_ERROR
        assert "/var/db/pw" not in result.response.answer
        assert result.traceability.request_id == "ERR-REQ-123"

        # Mode B: with raise_exceptions=True, propagates for HTTP route handler
        with pytest.raises(RuntimeError):
            adapter.execute_advice_rag(
                query="What is bribery?",
                raise_exceptions=True,
            )


# ==============================================================================
# 11. Citations and provenance remain attached
# ==============================================================================
def test_w54_citations_provenance_remain_attached(advice_adapter):
    """Test 11: Grounded advice results maintain rich, deterministic citations and provenance."""
    result = advice_adapter.execute_advice_rag(
        query="What procedures should commercial organisations implement to prevent bribery?",
    )
    assert len(result.citations) >= 1
    assert len(result.provenance) >= 1

    cit = result.citations[0]
    assert cit.citation_id.startswith("CIT-")
    assert cit.chunk_id.startswith("RR-")
    assert cit.formatted_citation.startswith("[")

    prov = result.provenance[0]
    assert prov.regulation != ""
    assert prov.official_source != ""
    assert prov.jurisdiction in ["UK", "EU"]


# ==============================================================================
# 12. Correlation / Request ID is preserved
# ==============================================================================
def test_w54_correlation_request_id_preserved(advice_adapter, api_client):
    """Test 12: Caller correlation ID is strictly preserved across in-process adapter and HTTP API."""
    corr_id = "ADV-CORR-778899"

    # In-process execution
    result = advice_adapter.execute_advice_rag(
        query="What constitutes bribery under Section 1?",
        request_id=corr_id,
    )
    assert result.traceability.request_id == corr_id
    assert result.response.request_id == corr_id

    # HTTP API execution
    api_resp = api_client.post(
        "/api/v1/query",
        json={
            "id": corr_id,
            "query": "What constitutes bribery under Section 1?",
            "advisor_advice_ids": ["ADV-001"],
        },
    )
    assert api_resp.status_code == 200
    data = api_resp.json()
    assert data["request_id"] == corr_id


# ==============================================================================
# 13. Unauthorized project context does not bypass authorization
# ==============================================================================
def test_w54_unauthorized_project_context_fails_closed(advice_adapter):
    """Test 13: Supplying an unassigned/foreign project ID fails closed, preventing data leakage."""
    result = advice_adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person?",
        project_id="ForeignProject-Unauthorized-999",
    )
    # Fails closed to INSUFFICIENT_EVIDENCE because 0 chunks match foreign tenant filter
    assert result.response.status == ResponseStatus.INSUFFICIENT_EVIDENCE
    assert result.response.grounded is False
    assert result.citations == []
    assert result.provenance == []


# ==============================================================================
# 14. Candidate regulatory records remain fail-closed
# ==============================================================================
def test_w54_candidate_records_remain_fail_closed(advice_adapter):
    """Test 14: All records are Candidate (0 Approved) and approval gating strictly holds."""
    result = advice_adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person?",
    )
    assert result.response.metadata.has_candidate_evidence is True
    assert result.response.metadata.approved_evidence_count == 0

    for cit in result.citations:
        assert cit.is_approved_for_rag is False
        assert cit.validation_status == "Candidate - Awaiting Approval"


# ==============================================================================
# 15. No legal / professional decision is automatically made
# ==============================================================================
def test_w54_no_legal_professional_decision_made(advice_adapter):
    """Test 15: Result contains non-adjudication disclaimer and reports relationships objectively."""
    result = advice_adapter.execute_advice_rag(
        query="How do the UK Bribery Act 2010 statutory offences relate to the Ministry of Justice Six Principles guidance?",
    )
    # Must contain prominent disclaimer
    assert "does not constitute formal legal" in result.disclaimer
    assert "qualified compliance professional" in result.disclaimer

    # If conflicts exist, non-adjudication message is explicit
    if result.conflicts:
        conflict = result.conflicts[0]
        assert "No legal conflict resolution is made by this system." in conflict.message
        assert conflict.requires_human_review is True
