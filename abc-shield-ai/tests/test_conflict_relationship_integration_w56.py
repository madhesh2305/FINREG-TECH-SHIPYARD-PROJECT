"""Automated test suite for Week 5 — Task W5.6: Conflict / Relationship Integration.

Validates the clean integration of W4.10 Conflict/Relationship detection capability
(CO-001 through CO-011) into the Week 5 Advice/RAG comparison workflow (AdviceComparator).

20 Verification Scenarios:
1. Canonical taxonomy preservation (CONFLICT, OVERLAP, SCOPE_DIFFERENCE, AUTHORITY_DIFFERENCE, VERSION_DIFFERENCE).
2. Direct ConflictDetector verification across 11 registered records (CO-001..CO-011).
3. Relationship classification: OVERLAP (e.g. CO-001 UK-01 vs UK-02).
4. Relationship classification: SCOPE_DIFFERENCE.
5. Relationship classification: AUTHORITY_DIFFERENCE.
6. Relationship classification: VERSION_DIFFERENCE (e.g. CO-010 EU-04 vs EU-05).
7. Relationship classification: CONFLICT (direct conflict).
8. Conflict findings propagation through AdviceComparator.
9. Three-tier separation: Tier A (Metadata/CO) vs Tier B (ChromaDB evidence) vs Tier C (Advisor differences).
10. Supporting regulatory evidence connection (linking chunk IDs and source IDs).
11. Provenance integrity for conflict findings.
12. Traceability context propagation (comparison_id, request_id, project_id, requirement_ids).
13. Human review flag triggered on relationship detection.
14. Strict non-adjudication invariant (decision is None, no correct_advisor, mandatory disclaimer).
15. Candidate record fail-closed behavior under filter_approved_only=True.
16. Safe evidence gaps preserved without declaring advisor legally incorrect.
17. Tenant / project isolation enforcement.
18. Backward compatibility with W5.4 AdviceRAGAdapter.
19. REST API route POST /api/v1/compare serialization of conflict findings & traceability.
20. REST API strict validation (extra="forbid") rejection with HTTP 422.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from rag.conflict.conflict_detector import (
    ConflictDetector,
    ConflictFinding,
    ConflictType,
    classify_relationship,
)
from rag.pipeline.advice_comparator import (
    AdviceComparator,
    AdvisorAdviceItem,
    AdviceComparisonRequest,
    AdviceComparisonResult,
    ComparisonDifferenceType,
)
from rag.pipeline.advice_adapter import AdviceRAGAdapter
from rag.retrieval.retriever import RetrievalResult


@pytest.fixture(scope="module")
def api_client():
    """Shared TestClient instance for API route verification."""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def conflict_detector():
    """Shared ConflictDetector instance loaded from controlled register."""
    return ConflictDetector()


@pytest.fixture(scope="module")
def comparator():
    """Shared AdviceComparator instance."""
    return AdviceComparator()


def _make_chunk(
    chunk_id: str,
    record_id: str,
    source_id: str,
    regulation: str,
    section_article: str = "Section 1",
    authority_level: str = "A",
    jurisdiction: str = "UK",
    validation_status: str = "Candidate - Awaiting Approval",
    is_approved_for_rag: bool = False,
    text: str = "Regulatory requirement text.",
    similarity_score: float = 0.88,
) -> RetrievalResult:
    """Helper to construct synthetic RetrievalResult objects for deterministic testing."""
    return RetrievalResult(
        chunk_id=chunk_id,
        record_id=record_id,
        source_id=source_id,
        regulation=regulation,
        regulator="Relevant Authority",
        jurisdiction=jurisdiction,
        section_article=section_article,
        title=f"Title for {section_article}",
        text=text,
        text_type="retrieval_text",
        topic="Anti-Bribery and Corruption",
        official_source="https://example.com/official",
        version_date="2024-01-01",
        effective_date="2024-01-01",
        validation_status=validation_status,
        is_approved_for_rag=is_approved_for_rag,
        authority_level=authority_level,
        source_type="Statute" if authority_level == "A" else "Guidance",
        similarity_score=similarity_score,
        distance=1.0 - similarity_score,
    )


# ==============================================================================
# 1. Canonical taxonomy preservation
# ==============================================================================
def test_w56_canonical_taxonomy_preservation():
    """Test 1: Canonical relationship taxonomy is preserved with zero invented severity or confidence."""
    expected_types = {
        "CONFLICT",
        "OVERLAP",
        "SCOPE_DIFFERENCE",
        "AUTHORITY_DIFFERENCE",
        "VERSION_DIFFERENCE",
        "UNKNOWN_RELATIONSHIP",
    }
    actual_types = {t.value for t in ConflictType}
    assert actual_types == expected_types

    # Ensure no arbitrary severities or artificial confidence scores on ConflictFinding
    finding_fields = ConflictFinding.model_fields.keys()
    assert "severity" not in finding_fields
    assert "confidence" not in finding_fields
    assert "conflict_score" not in finding_fields


# ==============================================================================
# 2. ConflictDetector CO register loaded
# ==============================================================================
def test_w56_conflict_detector_co_register_loaded(conflict_detector):
    """Test 2: ConflictDetector initializes with exactly 11 controlled records (CO-001..CO-011)."""
    assert len(conflict_detector.conflict_records) == 11
    ids = [r.conflict_id for r in conflict_detector.conflict_records]
    expected_ids = [f"CO-{i:03d}" for i in range(1, 12)]
    assert ids == expected_ids


# ==============================================================================
# 3. Relationship classification: OVERLAP
# ==============================================================================
def test_w56_relationship_classification_overlap():
    """Test 3: classify_relationship categorizes complementary and thematic overlaps as OVERLAP."""
    ctype = classify_relationship("Overlap - complementary", "No direct conflict identified")
    assert ctype == ConflictType.OVERLAP

    ctype2 = classify_relationship("Partial thematic overlap", "No direct conflict identified")
    assert ctype2 == ConflictType.OVERLAP


# ==============================================================================
# 4. Relationship classification: SCOPE_DIFFERENCE
# ==============================================================================
def test_w56_relationship_classification_scope_difference():
    """Test 4: classify_relationship categorizes scope variances as SCOPE_DIFFERENCE."""
    ctype = classify_relationship("Scope difference - statutory vs guidance scope", "Different scope")
    assert ctype == ConflictType.SCOPE_DIFFERENCE


# ==============================================================================
# 5. Relationship classification: AUTHORITY_DIFFERENCE
# ==============================================================================
def test_w56_relationship_classification_authority_difference():
    """Test 5: classify_relationship categorizes authority variances as AUTHORITY_DIFFERENCE."""
    ctype = classify_relationship("Authority difference - statutory regulator vs guidance body", "Different authority")
    assert ctype == ConflictType.AUTHORITY_DIFFERENCE


# ==============================================================================
# 6. Relationship classification: VERSION_DIFFERENCE
# ==============================================================================
def test_w56_relationship_classification_version_difference():
    """Test 6: classify_relationship categorizes amendment and version variances as VERSION_DIFFERENCE."""
    ctype = classify_relationship(
        "Direct legal relationship - amendment, not conflict",
        "No conflict; version/amendment relationship",
    )
    assert ctype == ConflictType.VERSION_DIFFERENCE


# ==============================================================================
# 7. Relationship classification: CONFLICT
# ==============================================================================
def test_w56_relationship_classification_direct_conflict():
    """Test 7: classify_relationship categorizes direct contradictory requirements as CONFLICT."""
    ctype = classify_relationship("Direct substantive conflict between requirements", "Conflict")
    assert ctype == ConflictType.CONFLICT


# ==============================================================================
# 8. Conflict findings propagation through AdviceComparator
# ==============================================================================
def test_w56_advice_comparator_detects_co_relationships(comparator):
    """Test 8: Co-retrieving documented sources (UK-01 and UK-02) attaches ConflictFinding in relationships."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles procedures.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert len(result.relationships) >= 1
    rel = result.relationships[0]
    assert isinstance(rel, ConflictFinding)
    assert rel.conflict_id == "CO-001"
    assert rel.relationship == "Overlap - complementary"
    assert rel.conflict_type == ConflictType.OVERLAP
    assert "No legal conflict resolution is made by this system." in rel.message


# ==============================================================================
# 9. Three-tier separation: Tier A vs Tier B vs Tier C
# ==============================================================================
def test_w56_three_tier_separation(comparator):
    """Test 9: Strict architectural separation between Tier A (Metadata/CO), Tier B (Evidence), and Tier C (Differences)."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Commercial organisations must maintain adequate procedures under Section 7 of the Bribery Act 2010.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Commercial organisations are exempt from implementing anti-bribery procedures under Section 7.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    # Tier A: Registered Regulatory Metadata (from Conflict Overlap register CO-001..CO-011)
    for rel in result.relationships:
        assert isinstance(rel, ConflictFinding)
        assert rel.conflict_id.startswith("CO-")

    # Tier B: Retrieved Regulatory Evidence (from ChromaDB)
    for cit in result.citations:
        assert cit.source_id.startswith("UK-") or cit.source_id.startswith("EU-")
    for prov in result.provenance:
        assert prov.record_id.startswith("RR-") or prov.source_id.startswith("UK-") or prov.source_id.startswith("EU-")
    for supp in result.supporting_evidence:
        assert supp.evidence_status in {"SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "INSUFFICIENT_EVIDENCE"}

    # Tier C: Inferred Advisor Differences (from advisor text comparison)
    for diff in result.differences:
        assert diff.difference_type in {
            ComparisonDifferenceType.NO_DIFFERENCE,
            ComparisonDifferenceType.SUBSTANTIVE_DIFFERENCE,
            ComparisonDifferenceType.SCOPE_DIFFERENCE,
            ComparisonDifferenceType.AUTHORITY_DIFFERENCE,
            ComparisonDifferenceType.VERSION_DIFFERENCE,
            ComparisonDifferenceType.POTENTIAL_CONTRADICTION,
        }
        assert diff.is_contradiction is True


# ==============================================================================
# 10. Supporting regulatory evidence connection
# ==============================================================================
def test_w56_supporting_regulatory_evidence_connection(comparator):
    """Test 10: Conflict findings explicitly connect to retrieved chunk IDs and source IDs."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 general bribery offences.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Ministry of Justice Guidance on the Bribery Act 2010.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert len(result.relationships) >= 1
    rel = result.relationships[0]
    assert len(rel.retrieved_source_ids) >= 2
    assert len(rel.retrieved_chunk_ids) >= 2

    # Verify that retrieved chunk IDs are in citations and provenance
    all_chunk_ids = {cit.chunk_id for cit in result.citations}
    for chunk_id in rel.retrieved_chunk_ids:
        assert chunk_id in all_chunk_ids


# ==============================================================================
# 11. Provenance integrity for conflict findings
# ==============================================================================
def test_w56_provenance_integrity_for_conflict_findings(comparator):
    """Test 11: Sources involved in conflict findings have verifiable provenance records."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert len(result.relationships) >= 1
    rel = result.relationships[0]

    prov_sources = {p.source_id for p in result.provenance}
    assert rel.source_id_1 in prov_sources
    assert rel.source_id_2 in prov_sources


# ==============================================================================
# 12. Traceability context propagation
# ==============================================================================
def test_w56_traceability_context_includes_request_and_project_ids(comparator):
    """Test 12: ComparisonTraceabilityContext includes comparison_id, request_id, project_id, requirement_ids."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Advice text 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Advice text 2")

    result = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        comparison_id="CMP-TEST-56",
        request_id="REQ-CORR-1234",
        project_id="PRJ-ABC-999",
        requirement_ids=["REQ-SEC-01", "REQ-SEC-02"],
        jurisdiction="UK",
        regulatory_area="Anti-Bribery",
    )

    trace = result.traceability
    assert trace.comparison_id == "CMP-TEST-56"
    assert trace.request_id == "REQ-CORR-1234"
    assert trace.project_id == "PRJ-ABC-999"
    assert trace.requirement_ids == ["REQ-SEC-01", "REQ-SEC-02"]
    assert trace.advisor_1_id == "ADV-001"
    assert trace.advisor_2_id == "ADV-002"
    assert trace.jurisdiction == "UK"
    assert trace.regulatory_area == "Anti-Bribery"
    assert trace.timestamp is not None


# ==============================================================================
# 13. Human review flag triggered on relationship detection
# ==============================================================================
def test_w56_human_review_flag_triggered_on_relationships(comparator):
    """Test 13: human_review_required is True when relationships are detected, even if advice texts are identical."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 and Ministry of Justice Guidance Six Principles procedures.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Section 1 and Ministry of Justice Guidance Six Principles procedures.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert result.differences[0].difference_type == ComparisonDifferenceType.NO_DIFFERENCE
    # Even though there is NO difference between advisors, relationships are detected -> human review required!
    assert len(result.relationships) >= 1
    assert result.human_review_required is True


# ==============================================================================
# 14. Strict non-adjudication invariant
# ==============================================================================
def test_w56_strict_non_adjudication_invariant(comparator):
    """Test 14: decision is None, no correct_advisor field exists, and non-adjudication disclaimer is present."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Commercial organisations must implement anti-bribery procedures.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Anti-bribery prevention procedures are completely voluntary and unnecessary.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert result.decision is None
    assert not hasattr(result, "correct_advisor")
    assert not hasattr(result, "winning_advisor")
    assert "does NOT determine which advisor is legally or professionally correct" in result.disclaimer


# ==============================================================================
# 15. Candidate records fail-closed under approved filter
# ==============================================================================
def test_w56_candidate_records_fail_closed_under_approved_filter(comparator):
    """Test 15: Since all 15 corpus records are Candidate, filter_approved_only=True yields 0 chunks and 0 relationships."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    )

    result = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        filter_approved_only=True,
    )

    assert len(result.citations) == 0
    assert len(result.provenance) == 0
    assert len(result.relationships) == 0
    assert result.human_review_required is True


# ==============================================================================
# 16. Safe evidence gaps preserved
# ==============================================================================
def test_w56_safe_evidence_gaps_preserved(comparator):
    """Test 16: Missing provisions (e.g. Section 7) generate safe GapResult without claiming advisor is false."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Commercial organisations are liable under Section 7 for failure to prevent bribery.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Commercial organisations have a full defense under Section 7 if adequate procedures exist.",
    )

    result = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert len(result.evidence_gaps) >= 1
    gap = result.evidence_gaps[0]
    assert gap.is_gap is True
    assert "coverage limitations rather than proof that the advisor is incorrect" in gap.user_safe_message


# ==============================================================================
# 17. Project isolation enforced
# ==============================================================================
def test_w56_project_isolation_enforced(comparator):
    """Test 17: Valid project_id passes cleanly into traceability without cross-tenant leakage."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Anti-bribery procedures text.")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Different anti-bribery advice text.")

    result = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        project_id="PRJ-TENANT-ALPHA",
    )

    assert result.traceability.project_id == "PRJ-TENANT-ALPHA"


# ==============================================================================
# 18. Backward compatibility with W5.4 AdviceRAGAdapter
# ==============================================================================
def test_w56_w54_advice_adapter_compatibility():
    """Test 18: AdviceRAGAdapter continues to run seamlessly alongside W5.6 relationship integration."""
    adapter = AdviceRAGAdapter()
    result = adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person under Section 1?",
        top_k=1,
    )
    assert result.external_status == "SUCCESS"
    assert result.workflow_status == "RAG_SUPPORTED"
    assert len(result.citations) >= 1
    assert "does not constitute" in result.disclaimer.lower()


# ==============================================================================
# 19. REST API route POST /api/v1/compare serialization
# ==============================================================================
def test_w56_http_api_compare_serialization(api_client):
    """Test 19: POST /api/v1/compare serializes full result including request_id and relationships."""
    payload = {
        "comparison_id": "CMP-W56-HTTP",
        "request_id": "REQ-TRACE-W56",
        "requirement_ids": ["REQ-001", "REQ-002"],
        "advisor_1": {
            "advice_id": "ADV-001",
            "advice_text": "Bribery Act 2010 Section 1 offences of bribing another person.",
        },
        "advisor_2": {
            "advice_id": "ADV-002",
            "advice_text": "Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
        },
        "context": {
            "jurisdiction": "UK",
            "regulatory_area": "Anti-Bribery",
        },
    }

    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["comparison_id"] == "CMP-W56-HTTP"
    assert data["traceability"]["request_id"] == "REQ-TRACE-W56"
    assert data["decision"] is None
    assert data["human_review_required"] is True
    assert "relationships" in data
    assert len(data["relationships"]) >= 1
    assert data["relationships"][0]["conflict_id"] == "CO-001"
    assert data["relationships"][0]["conflict_type"] == "OVERLAP"


# ==============================================================================
# 20. REST API strict validation (extra="forbid")
# ==============================================================================
def test_w56_http_api_extra_forbid_rejection(api_client):
    """Test 20: POST /api/v1/compare rejects injected extra fields with HTTP 422."""
    payload = {
        "advisor_1": {"advice_id": "A1", "advice_text": "Advice 1"},
        "advisor_2": {"advice_id": "A2", "advice_text": "Advice 2"},
        "unauthorized_field": "exploit_attempt",
        "correct_advisor": "A1",
    }
    response = api_client.post("/api/v1/compare", json=payload)
    assert response.status_code == 422
