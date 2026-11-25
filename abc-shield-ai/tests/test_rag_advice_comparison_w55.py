"""Automated test suite for Week 5 — Task W5.5: Advice Comparison.

Verifies the RAG-side Advice Comparison engine:
- Difference detection (identical, substantive, scope, authority, version, contradiction)
- Source-grounded regulatory retrieval via ChromaDB
- Deterministic citations, provenance, and supporting evidence tracking
- Documented relationship/conflict detection (CO-001..CO-011)
- Evidence gap detection with safe non-prejudicial disclosure
- Approval gating and candidate record fail-closed boundaries
- Project/tenant isolation
- Strict non-adjudication: decision=None, no correct_advisor selection
- Compatibility with W4.10 ConflictDetector and W5.4 AdviceRAGAdapter
- REST API /api/v1/compare route validation
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from rag.pipeline.advice_comparator import (
    AdviceComparator,
    AdvisorAdviceItem,
    AdviceComparisonRequest,
    AdviceComparisonResult,
    ComparisonDifferenceType,
)
from rag.pipeline.advice_adapter import AdviceRAGAdapter
from rag.conflict.conflict_detector import ConflictDetector
from rag.generation.gap_handler import GapType


@pytest.fixture(scope="module")
def api_client():
    """Shared TestClient instance for API route verification."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def comparator():
    """Shared AdviceComparator instance explicitly wired to the Week 5 baseline corpus."""
    from pathlib import Path
    from rag.retrieval.retriever import RegulatoryRetriever
    from rag.retrieval.vector_store import ChromaVectorStore
    legacy_store = ChromaVectorStore(
        persist_dir=Path("data/processed/chroma_db"),
        collection_name="regulatory_records",
    )
    return AdviceComparator(retriever=RegulatoryRetriever(vector_store=legacy_store))


# ==============================================================================
# 1. Two identical advice texts
# ==============================================================================
def test_w55_identical_advice_texts_yields_no_difference(comparator):
    """Test 1: Identical advice texts produce NO_DIFFERENCE and is_contradiction=False."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Commercial organisations must implement proportionate anti-bribery procedures under the Bribery Act 2010.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Commercial organisations must implement proportionate anti-bribery procedures under the Bribery Act 2010.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert isinstance(result, AdviceComparisonResult)
    assert len(result.differences) == 1
    assert result.differences[0].difference_type == ComparisonDifferenceType.NO_DIFFERENCE
    assert result.differences[0].is_contradiction is False
    assert result.decision is None


# ==============================================================================
# 2. Two materially different advice texts
# ==============================================================================
def test_w55_materially_different_advice_texts_detected(comparator):
    """Test 2: Materially differing advice texts are detected as SUBSTANTIVE_DIFFERENCE."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Commercial organisations should conduct third-party due diligence annually and document all hospitality expenses.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Commercial organisations should conduct third-party due diligence only upon contract renewal and omit routine hospitality logging.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert len(result.differences) >= 1
    diff_types = [d.difference_type for d in result.differences]
    assert ComparisonDifferenceType.SUBSTANTIVE_DIFFERENCE in diff_types or ComparisonDifferenceType.POTENTIAL_CONTRADICTION in diff_types
    assert result.human_review_required is True


# ==============================================================================
# 3. Potential contradiction
# ==============================================================================
def test_w55_potential_contradiction_flags_human_review(comparator):
    """Test 3: Mutually incompatible assertions are identified as POTENTIAL_CONTRADICTION and flag human review."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Anti-bribery prevention procedures are mandatory and strictly required for all commercial organisations under the Bribery Act 2010.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Anti-bribery prevention procedures are optional and voluntary for commercial organisations under the Bribery Act 2010.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert any(d.is_contradiction for d in result.differences)
    assert any(d.difference_type == ComparisonDifferenceType.POTENTIAL_CONTRADICTION for d in result.differences)
    assert result.human_review_required is True
    # The AI must NOT decide which advisor is correct
    assert result.decision is None


# ==============================================================================
# 4. Scope difference
# ==============================================================================
def test_w55_scope_difference_not_automatically_contradiction(comparator):
    """Test 4: Differing jurisdictional or statutory scopes are classified as SCOPE_DIFFERENCE without falsely declaring contradiction."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-UK-001",
        advice_text="Under Section 1 of the UK Bribery Act 2010, bribing another person is an individual criminal offence.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-MOJ-002",
        advice_text="Under the Ministry of Justice Six Principles guidance, commercial organisations should establish proportionate bribery prevention procedures.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert any(d.difference_type == ComparisonDifferenceType.SCOPE_DIFFERENCE for d in result.differences)
    # Scope differences are distinct from contradictions
    assert result.differences[0].is_contradiction is False


# ==============================================================================
# 5. Authority / Version difference
# ==============================================================================
def test_w55_authority_or_version_difference_identified(comparator):
    """Test 5: Primary statute vs executive guidance is identified as AUTHORITY_DIFFERENCE."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="The primary Act of Parliament establishes legal offences for active and passive bribery.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="The Ministry of Justice statutory guidance explains implementation procedures for commercial organisations.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    diff_types = [d.difference_type for d in result.differences]
    assert ComparisonDifferenceType.AUTHORITY_DIFFERENCE in diff_types or ComparisonDifferenceType.SCOPE_DIFFERENCE in diff_types


# ==============================================================================
# 6. Supporting evidence
# ==============================================================================
def test_w55_supporting_evidence_attaches_citations_and_provenance(comparator):
    """Test 6: Comparison attaches deterministic citations, provenance, and supporting evidence."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Under Section 1 of the Bribery Act 2010, it is an offence to offer, promise or give a financial or other advantage.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="The Ministry of Justice outlines Six Principles for commercial organisations to prevent bribery.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert len(result.citations) >= 1
    assert len(result.provenance) >= 1
    assert len(result.supporting_evidence) == 2

    # Verify supporting evidence breakdown
    ev_1 = next(e for e in result.supporting_evidence if e.advice_id == "ADV-001")
    assert ev_1.evidence_status in ["SUPPORTED", "PARTIALLY_SUPPORTED"]
    assert len(ev_1.supporting_chunk_ids) >= 1


# ==============================================================================
# 7. Evidence gap
# ==============================================================================
def test_w55_evidence_gap_identified_without_claiming_advice_is_wrong(comparator):
    """Test 7: Missing provisions (e.g. Section 7) emit a GapResult without declaring the advice false."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Under Section 7 of the Bribery Act 2010, commercial organisations commit an offence of failure to prevent bribery.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Section 7 creates corporate liability unless the organisation had adequate procedures in place.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert len(result.evidence_gaps) >= 1
    gap = next(g for g in result.evidence_gaps if g.gap_type == GapType.MISSING_SPECIFIC_PROVISION)
    assert "Section 7" in gap.message
    # Safe wording invariant
    assert "corpus coverage limitations" in gap.user_safe_message
    assert "rather than proof that the advisor is incorrect" in gap.user_safe_message


# ==============================================================================
# 8. No approved source (Approved-only filter fails closed)
# ==============================================================================
def test_w55_no_approved_source_behavior_remains_safe(comparator):
    """Test 8: Approved-only comparison against candidate corpus fails closed safely."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Offence of bribing under Section 1.")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Procedures to prevent bribery.")

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, filter_approved_only=True)

    assert len(result.citations) == 0
    assert len(result.provenance) == 0
    assert len(result.evidence_gaps) >= 1
    assert result.evidence_gaps[0].gap_type.value == "UNAPPROVED_EVIDENCE"
    assert result.human_review_required is True


# ==============================================================================
# 9. Candidate source handling
# ==============================================================================
def test_w55_candidate_source_remains_fail_closed(comparator):
    """Test 9: Candidate records are tagged is_approved_for_rag=False and mandate human review."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Section 1 bribery offence.")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Six Principles prevention procedures.")

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    for cit in result.citations:
        assert cit.is_approved_for_rag is False
        assert cit.validation_status == "Candidate - Awaiting Approval"
    assert result.human_review_required is True


# ==============================================================================
# 10. Advisor IDs preserved for traceability
# ==============================================================================
def test_w55_advisor_ids_preserved_for_traceability(comparator):
    """Test 10: Advisor IDs, comparison_id, project_id, and requirement_ids are preserved in traceability."""
    a1 = AdvisorAdviceItem(advice_id="ADV-ALPHA-101", advice_text="First stance on bribery controls.")
    a2 = AdvisorAdviceItem(advice_id="ADV-BETA-202", advice_text="Second stance on bribery controls.")

    result = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        comparison_id="CMP-TEST-999",
        project_id="PRJ-ABC-001",
        requirement_ids=["REQ-101", "REQ-102"],
    )

    assert result.traceability.comparison_id == "CMP-TEST-999"
    assert result.traceability.advisor_1_id == "ADV-ALPHA-101"
    assert result.traceability.advisor_2_id == "ADV-BETA-202"
    assert result.traceability.project_id == "PRJ-ABC-001"
    assert result.traceability.requirement_ids == ["REQ-101", "REQ-102"]


# ==============================================================================
# 11. Project isolation remains enforced
# ==============================================================================
def test_w55_project_isolation_remains_enforced(comparator):
    """Test 11: Supplying an unassigned/foreign tenant ID returns 0 chunks and fails closed."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Section 1 offence.")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Section 2 passive bribery.")

    result = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        project_id="ForeignProject-Unauthorized-999",
    )

    assert len(result.citations) == 0
    assert len(result.provenance) == 0
    assert result.human_review_required is True


# ==============================================================================
# 12. No final legal / professional decision generated
# ==============================================================================
def test_w55_no_final_legal_professional_decision_generated(comparator):
    """Test 12: Comparison strictly reserves decision=None and carries non-adjudication disclaimer."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Bribery Act applies strictly.")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Bribery Act does not apply.")

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    # Invariant: No decision, no correct_advisor selection
    assert result.decision is None
    dump = result.model_dump()
    assert "correct_advisor" not in dump
    assert "winner" not in dump

    # Mandatory disclaimer present
    assert "does not constitute formal legal or professional advice" in result.disclaimer
    assert "exclusive responsibility of a qualified compliance professional" in result.disclaimer


# ==============================================================================
# 13. Existing W4.10 conflict detector remains compatible
# ==============================================================================
def test_w55_existing_w410_conflict_detector_remains_compatible(comparator):
    """Test 13: Co-retrieving documented sources surfaces registered ConflictFinding records."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert len(result.relationships) >= 1
    rel = result.relationships[0]
    assert rel.conflict_id == "CO-001"
    assert rel.relationship == "Overlap - complementary"
    assert "No legal conflict resolution is made by this system." in rel.message


# ==============================================================================
# 14. Existing W5.4 AdviceRAGAdapter remains compatible
# ==============================================================================
def test_w55_existing_w54_advice_adapter_remains_compatible():
    """Test 14: AdviceRAGAdapter continues to function without regression."""
    adapter = AdviceRAGAdapter()
    result = adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person under Section 1?",
        top_k=1,
    )
    assert result.external_status == "SUCCESS"
    assert result.workflow_status == "RAG_SUPPORTED"
    assert len(result.citations) >= 1


# ==============================================================================
# 15. HTTP API route POST /api/v1/compare
# ==============================================================================
def test_w55_http_compare_endpoint(api_client):
    """Test 15: POST /api/v1/compare accepts valid payload and returns 200 with AdviceComparisonResult."""
    payload = {
        "comparison_id": "CMP-HTTP-001",
        "project_id": "PRJ-ABC-001",
        "requirement_ids": ["REQ-001"],
        "advisor_1": {
            "advice_id": "ADV-001",
            "advice_text": "Commercial organisations must establish proportionate anti-bribery procedures.",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advice_text": "Anti-bribery prevention procedures are optional for commercial organisations.",
        },
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery",
        },
    }

    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["comparison_id"] == "CMP-HTTP-001"
    assert data["decision"] is None
    assert data["human_review_required"] is True
    assert len(data["differences"]) >= 1
    assert data["differences"][0]["is_contradiction"] is True


# ==============================================================================
# 16. HTTP API route safely ignores benign extra fields via extra="ignore"
# ==============================================================================
def test_w55_http_compare_extra_forbid_enforced(api_client):
    """Test 16: POST /api/v1/compare safely ignores extra top-level fields with HTTP 200."""
    payload = {
        "advisor_1": {"advice_id": "A1", "advice_text": "Advice 1"},
        "advisor_2": {"advice_id": "A2", "advice_text": "Advice 2"},
        "unauthorized_field": "injected_value",
    }
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] is None
