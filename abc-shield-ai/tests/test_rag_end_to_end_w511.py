"""Automated test suite for Week 5 — Task W5.11: Final End-to-End RAG Verification.

Verifies the complete end-to-end integration of the AI/RAG system within the product workflow:
Project -> Requirement -> Advisor 1 + Advisor 2 -> RAG Evidence Retrieval ->
Grounded Response -> Citations + Provenance -> Advice Comparison ->
Differences / Relationships / Evidence Gaps -> Human Review -> Decision=None ->
Traceability / Audit Lineage.

Strict Scope Boundaries:
- Padma owns: RAG, retrieval, grounding, citations, provenance, gap handling,
  conflict/relationship detection, AdviceRAGAdapter, AdviceComparator, RAG traceability.
- Vishal owns: Authentication, project lifecycle, requirement/advisor persistence, PostgreSQL DB.
- Harshini owns: Frontend UI and rendering.
- Madhesh owns: Regulatory source data & SME approval governance.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models.query import QueryRequest
from rag.pipeline.advice_adapter import (
    AdviceRAGAdapter,
    AdviceRAGResult,
    AdviceWorkflowStatus,
)
from rag.pipeline.advice_comparator import (
    AdviceComparator,
    AdvisorAdviceItem,
    AdviceComparisonRequest,
    AdviceComparisonResult,
    ComparisonDifferenceType,
)
from rag.output.structured_response import ResponseStatus, StructuredAIResponse
from rag.conflict.conflict_detector import ConflictType
from rag.generation.gap_handler import GapType
from rag.retrieval.retriever import RegulatoryRetriever


@pytest.fixture(scope="module")
def api_client():
    """Shared FastAPI TestClient for end-to-end wire testing."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def advice_adapter():
    """Shared AdviceRAGAdapter instance."""
    return AdviceRAGAdapter()


@pytest.fixture(scope="module")
def comparator():
    """Shared AdviceComparator instance."""
    return AdviceComparator()


@pytest.fixture(scope="module")
def canonical_corpus_data():
    """Loads canonical processed records and chunks for lineage auditing."""
    records_path = Path("data/processed/normalized_regulatory_records.json")
    chunks_path = Path("data/processed/regulatory_chunks.json")
    with open(records_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return {
        "records": {r["record_id"]: r for r in records},
        "chunks": {c["chunk_id"]: c for c in chunks},
    }


# ==============================================================================
# 1. Grounded Advice Workflow E2E
# ==============================================================================
def test_w511_grounded_advice_workflow_e2e(advice_adapter):
    """Scenario 1: Requirement ID, advisor advice ID, and query flow cleanly into grounded advice with traceability."""
    request = QueryRequest(
        id="REQ-E2E-001",
        query="What procedures must commercial organisations implement to prevent bribery under the UK Bribery Act 2010?",
        requirement_ids=["REQ-001"],
        advisor_advice_ids=["ADV-UK-001"],
        context={"jurisdiction": "UK", "regulatory_area": "Anti-Bribery and Corruption"},
    )

    result = advice_adapter.execute_from_request(request)

    assert isinstance(result, AdviceRAGResult)
    # Correlation preservation
    assert result.traceability.request_id == "REQ-E2E-001"
    assert result.traceability.requirement_ids == ["REQ-001"]
    assert result.traceability.advisor_advice_ids == ["ADV-UK-001"]
    assert result.traceability.jurisdiction == "UK"

    # Status mapping
    assert result.response.status == ResponseStatus.GROUNDED
    assert result.external_status in ["SUCCESS", "CONFLICT_DETECTED"]
    assert result.workflow_status in [AdviceWorkflowStatus.RAG_SUPPORTED, AdviceWorkflowStatus.RAG_REVIEW_REQUIRED]

    # Grounded response & Citations
    assert len(result.answer) > 0
    assert len(result.citations) > 0
    assert len(result.provenance) == len(result.citations)

    # Candidate status & non-adjudication
    assert result.response.metadata.has_candidate_evidence is True
    assert result.requires_human_review is True
    for cit in result.citations:
        assert cit.validation_status == "Candidate - Awaiting Approval"
        assert cit.is_approved_for_rag is False
    assert "does not constitute formal legal" in result.disclaimer

    # Evidence trace helper
    trace = result.get_evidence_trace()
    assert trace["request_id"] == "REQ-E2E-001"
    assert len(trace["citations"]) == len(result.citations)


# ==============================================================================
# 2. Advice Comparison E2E
# ==============================================================================
def test_w511_advice_comparison_e2e(comparator):
    """Scenario 2: Comparing two advisor positions identifies contradictions, attaches evidence, and requires human review."""
    request = AdviceComparisonRequest(
        comparison_id="CMP-E2E-001",
        request_id="REQ-CMP-001",
        requirement_ids=["REQ-001"],
        advisor_1=AdvisorAdviceItem(
            advice_id="ADV-001",
            advisor_name="Lead Compliance Officer",
            advice_text="Commercial organisations must implement proportionate anti-bribery procedures, risk assessment, and due diligence under the UK Bribery Act 2010.",
            source_reference="Bribery Act 2010 Section 7",
        ),
        advisor_2=AdvisorAdviceItem(
            advice_id="ADV-002",
            advisor_name="External Defense Counsel",
            advice_text="Commercial organisations face strict liability under Section 7 and compliance prevention procedures are completely voluntary and optional.",
            source_reference="Bribery Act 2010 Section 7",
        ),
        context={"jurisdiction": "UK", "regulatory_area": "Anti-Bribery and Corruption"},
    )

    result = comparator.compare_from_request(request)

    assert isinstance(result, AdviceComparisonResult)
    # Correlation preservation
    assert result.comparison_id == "CMP-E2E-001"
    assert result.traceability.request_id == "REQ-CMP-001"
    assert result.traceability.requirement_ids == ["REQ-001"]
    assert result.traceability.advisor_1_id == "ADV-001"
    assert result.traceability.advisor_2_id == "ADV-002"

    # Difference detection: polarity contradiction (mandatory vs voluntary/optional)
    assert len(result.differences) > 0
    contradictions = [d for d in result.differences if d.is_contradiction]
    assert len(contradictions) >= 1
    assert contradictions[0].difference_type == ComparisonDifferenceType.POTENTIAL_CONTRADICTION

    # Supporting evidence breakdown
    assert len(result.supporting_evidence) == 2
    adv1_supp = next(s for s in result.supporting_evidence if s.advice_id == "ADV-001")
    assert adv1_supp.evidence_status in ["SUPPORTED", "PARTIALLY_SUPPORTED"]
    assert len(adv1_supp.supporting_chunk_ids) > 0

    # Human review & Non-adjudication
    assert result.human_review_required is True
    assert result.decision is None
    assert "does not constitute formal legal" in result.disclaimer
    assert "Final legal determinations" in result.disclaimer


# ==============================================================================
# 3. Citation and Provenance Audit Lineage E2E
# ==============================================================================
def test_w511_citation_and_provenance_audit_lineage_e2e(advice_adapter, canonical_corpus_data):
    """Scenario 3: 1:1 audit lineage from Answer -> Citation -> Chunk -> Record -> Source -> Official Source."""
    request = QueryRequest(
        id="REQ-E2E-AUDIT",
        query="What are the six principles for bribery prevention under UK Ministry of Justice guidance?",
        context={"jurisdiction": "UK"},
    )
    result = advice_adapter.execute_from_request(request)

    assert len(result.citations) > 0
    records_dict = canonical_corpus_data["records"]
    chunks_dict = canonical_corpus_data["chunks"]

    for citation, prov in zip(result.citations, result.provenance):
        # 1. Chunk ID must resolve in canonical chunks
        assert citation.chunk_id in chunks_dict
        chunk_obj = chunks_dict[citation.chunk_id]

        # 2. Record ID must match canonical record
        assert prov.record_id == chunk_obj["record_id"]
        assert prov.record_id in records_dict
        record_obj = records_dict[prov.record_id]

        # 3. Provenance and citation metadata integrity
        assert citation.chunk_id == prov.chunk_id
        assert citation.source_id == prov.source_id
        assert prov.source_id == record_obj["source_id"]
        assert citation.regulation == record_obj["regulation"]
        assert citation.jurisdiction == record_obj["jurisdiction"]

        # 4. Strict candidate approval lineage
        assert citation.validation_status == "Candidate - Awaiting Approval"
        assert prov.validation_status == "Candidate - Awaiting Approval"
        assert prov.is_approved_for_rag is False

        # 5. Canonical official source URL verification (no fabrication)
        if citation.official_source is not None:
            assert citation.official_source == record_obj["official_source"]
            assert citation.official_source.startswith("https://")


# ==============================================================================
# 4. Conflict / Relationship Integration E2E
# ==============================================================================
def test_w511_conflict_relationship_integration_e2e(comparator):
    """Scenario 4: Co-retrieving Section 7 and MOJ Guidance detects CO-001 OVERLAP with full trace."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-REL-01",
        advice_text="Bribery Act 2010 Section 7 creates the criminal offence of failure of commercial organisations to prevent bribery.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-REL-02",
        advice_text="Ministry of Justice adequate procedures guidance provides six principles for prevention procedures under Section 9.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, jurisdiction="UK")

    assert len(result.relationships) >= 1
    co001_finding = next((r for r in result.relationships if r.conflict_id == "CO-001"), None)
    assert co001_finding is not None
    assert co001_finding.conflict_type == ConflictType.OVERLAP
    assert "Overlap" in co001_finding.relationship
    assert co001_finding.source_id_1 == "UK-01"
    assert co001_finding.source_id_2 == "UK-02"

    # Traceability helper verification
    trace = result.get_conflict_trace("CO-001")
    assert trace is not None
    assert trace["conflict_id"] == "CO-001"
    assert trace["conflict_type"] == ConflictType.OVERLAP
    assert len(trace["retrieved_chunk_ids"]) >= 2
    assert len(trace["citations"]) >= 2
    assert len(trace["provenance"]) >= 2


# ==============================================================================
# 5. Evidence Gap and No-Source Path E2E
# ==============================================================================
def test_w511_evidence_gap_and_no_source_path_e2e(advice_adapter):
    """Scenario 5: Missing specific provisions trigger safe non-prejudicial GAP_DETECTED handling without hallucination."""
    request = QueryRequest(
        id="REQ-E2E-GAP",
        query="What are the specific requirements for offshore trust registration under Section 7 of the Bribery Act 2010?",
        context={"jurisdiction": "UK"},
    )

    result = advice_adapter.execute_from_request(request)

    assert result.response.status in [ResponseStatus.INSUFFICIENT_EVIDENCE, ResponseStatus.OUT_OF_SCOPE]
    assert result.external_status in ["GAP_DETECTED", "NO_SOURCE_FOUND"]
    assert result.workflow_status in [AdviceWorkflowStatus.RAG_GAP_DETECTED, AdviceWorkflowStatus.RAG_NO_SOURCES]

    # Gap object verification
    assert result.response.gap is not None
    assert result.response.gap.gap_type in [GapType.MISSING_SPECIFIC_PROVISION, GapType.OUT_OF_SCOPE]
    assert result.response.gap.coverage_nature == "CORPUS_COVERAGE_LIMITATION"

    # Guardrails: no fabricated trust registration citations, human review mandatory, no legal adjudication
    assert result.requires_human_review is True
    assert "does not constitute formal legal" in result.disclaimer
    for cit in result.citations:
        assert "trust registration" not in cit.title.lower()


# ==============================================================================
# 6. End-to-End Traceability Navigation
# ==============================================================================
def test_w511_end_to_end_traceability_navigation(comparator):
    """Scenario 6: Complete traceability navigation links advice IDs, comparison IDs, chunks, and citations."""
    request = AdviceComparisonRequest(
        comparison_id="CMP-NAV-001",
        request_id="REQ-NAV-001",
        requirement_ids=["REQ-001", "REQ-002"],
        advisor_1=AdvisorAdviceItem(
            advice_id="ADV-A",
            advice_text="Commercial organisations must implement proportionate anti-bribery procedures.",
        ),
        advisor_2=AdvisorAdviceItem(
            advice_id="ADV-B",
            advice_text="Proportionate procedures are guided by Ministry of Justice six principles.",
        ),
        context={"jurisdiction": "UK"},
    )

    result = comparator.compare_from_request(request)

    # 1. Full traceability summary
    summary = result.get_full_traceability_summary()
    assert summary["comparison_id"] == "CMP-NAV-001"
    assert summary["request_id"] == "REQ-NAV-001"
    assert summary["requirement_ids"] == ["REQ-001", "REQ-002"]
    assert summary["advisor_1_id"] == "ADV-A"
    assert summary["advisor_2_id"] == "ADV-B"
    assert summary["is_adjudicated"] is False
    assert summary["decision"] is None

    # 2. Advice-level trace navigation
    adv_a_trace = result.get_evidence_trace_for_advice("ADV-A")
    assert adv_a_trace is not None
    assert adv_a_trace["advice_id"] == "ADV-A"
    assert len(adv_a_trace["supporting_chunk_ids"]) > 0

    adv_b_trace = result.get_evidence_trace_for_advice("ADV-B")
    assert adv_b_trace is not None
    assert adv_b_trace["advice_id"] == "ADV-B"


# ==============================================================================
# 7. Strict Non-Adjudication Invariant
# ==============================================================================
def test_w511_strict_non_adjudication_invariant(comparator):
    """Scenario 7: The RAG comparison engine never declares a winner or selects an advisor (decision=None)."""
    scenarios = [
        # Identical
        ("Mandatory procedures required.", "Mandatory procedures required."),
        # Contradiction
        ("Mandatory compliance required.", "Optional compliance discretionary."),
        # Scope difference
        ("UK Bribery Act criminal offence.", "EU Directive AML standards."),
    ]

    for t1, t2 in scenarios:
        res = comparator.compare_advice(
            advisor_1=AdvisorAdviceItem(advice_id="A1", advice_text=t1),
            advisor_2=AdvisorAdviceItem(advice_id="A2", advice_text=t2),
        )
        assert res.decision is None, f"Decision must strictly be None for {t1} vs {t2}"
        assert "does not constitute formal legal" in res.disclaimer
        assert "does NOT determine which advisor is legally or professionally correct" in res.disclaimer


# ==============================================================================
# 8. Approval Gating Fail-Closed E2E
# ==============================================================================
def test_w511_approval_gating_fail_closed_e2e(comparator):
    """Scenario 8: filter_approved_only=True returns zero records and candidate evidence is never promoted."""
    retriever = RegulatoryRetriever()
    approved_chunks = retriever.retrieve(
        query="Bribery Act 2010 commercial organisations",
        filter_approved_only=True,
    )
    # Fail-closed: exactly 0 approved chunks in candidate-only corpus
    assert len(approved_chunks) == 0

    # Comparison under filter_approved_only=True fails closed with INSUFFICIENT/UNSUPPORTED
    res = comparator.compare_advice(
        advisor_1=AdvisorAdviceItem(advice_id="A1", advice_text="Bribery Act requirements apply."),
        advisor_2=AdvisorAdviceItem(advice_id="A2", advice_text="Bribery Act procedures voluntary."),
        filter_approved_only=True,
    )
    for supp in res.supporting_evidence:
        assert supp.evidence_status in ["UNSUPPORTED", "INSUFFICIENT_EVIDENCE"]
        assert len(supp.supporting_chunk_ids) == 0


# ==============================================================================
# 9. Tenant Isolation & Project ID Correlation E2E
# ==============================================================================
def test_w511_tenant_isolation_and_correlation_e2e(advice_adapter):
    """Scenario 9: project_id is preserved in traceability while unassigned tenant queries fail-closed safely."""
    request = QueryRequest(
        id="REQ-TENANT-001",
        project_id="PRJ-ABC-001",
        query="What is the offence under Section 1?",
        requirement_ids=["REQ-001"],
    )
    result = advice_adapter.execute_from_request(request)

    # 1. Project ID strictly captured in correlation traceability
    assert result.traceability.request_id == "REQ-TENANT-001"
    assert result.traceability.project_id == "PRJ-ABC-001"
    assert result.traceability.requirement_ids == ["REQ-001"]

    # 2. Fail-closed tenant isolation: no unassigned canonical records leaked to tenant filter
    assert len(result.response.retrieved_evidence) == 0
    assert result.response.status == ResponseStatus.INSUFFICIENT_EVIDENCE
    assert result.external_status in ["NO_SOURCE_FOUND", "GAP_DETECTED"]


# ==============================================================================
# 10. Frontend and Backend Handoff Contract E2E
# ==============================================================================
def test_w511_frontend_backend_handoff_contract_e2e(api_client):
    """Scenario 10: REST API /query and /compare return complete payloads required by Harshini & Vishal."""
    # 1. Query endpoint handoff
    query_payload = {
        "id": "REQ-HANDOFF-001",
        "query": "What are the six principles under Ministry of Justice guidance?",
        "requirement_ids": ["REQ-001"],
        "advisor_advice_ids": ["ADV-001"],
        "context": {"jurisdiction": "UK"},
    }
    q_resp = api_client.post("/api/v1/query", json=query_payload)
    assert q_resp.status_code == 200
    q_data = q_resp.json()

    # Required fields for Harshini & Vishal
    assert "answer" in q_data
    assert "status" in q_data
    assert "citations" in q_data
    assert "provenance" in q_data
    assert "conflicts" in q_data
    assert "gap" in q_data
    assert "retrieved_evidence" in q_data
    assert "metadata" in q_data
    assert q_data["metadata"]["has_candidate_evidence"] is True
    assert q_data["metadata"]["requires_human_review"] is True
    assert q_data["request_id"] == "REQ-HANDOFF-001"

    # 2. Compare endpoint handoff
    compare_payload = {
        "comparison_id": "CMP-HANDOFF-001",
        "request_id": "REQ-HANDOFF-001",
        "project_id": "PRJ-ABC-001",
        "requirement_ids": ["REQ-001"],
        "advisor_1": {
            "advice_id": "ADV-001",
            "advice_text": "Proportionate procedures must be implemented.",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advice_text": "Procedures are optional and voluntary.",
        },
    }
    c_resp = api_client.post("/api/v1/compare", json=compare_payload)
    assert c_resp.status_code == 200
    c_data = c_resp.json()

    # Required comparison fields
    assert c_data["comparison_id"] == "CMP-HANDOFF-001"
    assert "advisor_1" in c_data
    assert "advisor_2" in c_data
    assert "differences" in c_data
    assert "relationships" in c_data
    assert "supporting_evidence" in c_data
    assert "citations" in c_data
    assert "provenance" in c_data
    assert "evidence_gaps" in c_data
    assert "human_review_required" in c_data
    assert c_data["decision"] is None
    assert "disclaimer" in c_data
    assert "traceability" in c_data
    assert c_data["traceability"]["comparison_id"] == "CMP-HANDOFF-001"
    assert c_data["traceability"]["request_id"] == "REQ-HANDOFF-001"
    assert c_data["traceability"]["project_id"] == "PRJ-ABC-001"


# ==============================================================================
# 11. Failure Path Safe Handling E2E
# ==============================================================================
def test_w511_failure_path_safe_handling_e2e(api_client):
    """Scenario 11: Invalid queries or unauthorized payload injections fail safely with HTTP 422 without data leaks."""
    # Empty query rejection
    r1 = api_client.post("/api/v1/query", json={"query": "   "})
    assert r1.status_code == 422
    assert "detail" in r1.json()

    # Forbidden extra field injection
    r2 = api_client.post("/api/v1/query", json={"query": "test query", "unauthorized_admin_flag": True})
    assert r2.status_code == 422
    assert "detail" in r2.json()

    # Compare empty advice rejection
    r3 = api_client.post("/api/v1/compare", json={
        "advisor_1": {"advice_id": "A1", "advice_text": ""},
        "advisor_2": {"advice_id": "A2", "advice_text": "Valid text"},
    })
    assert r3.status_code == 422
    assert "detail" in r3.json()
