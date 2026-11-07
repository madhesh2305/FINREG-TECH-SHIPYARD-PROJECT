"""Automated evaluation and regression test suite for Week 5 — Task W5.9.

Validates the 14 critical dimensions of the integrated Week 5 RAG system:
1. Retrieval baseline concordance (matches W4.7 baseline metrics: P@1=0.9048, R@1=0.7381, HitRate@1=0.9048, MRR=0.9524).
2. Source grounding fidelity (answers supported by chunks, candidate warning/caveat preserved).
3. Citation correctness and authentic metadata (no fabricated URLs or identifiers).
4. Provenance lineage integrity (full audit trail, zero internal credential leaks).
5. Evidence gap safe disclosure (safe coverage limitation without accusing advisor/client).
6. No-source handling (NO_SOURCE_FOUND external status or safe gap, zero hallucinated statutes).
7. Unsupported out-of-corpus question handling (graceful boundary enforcement).
8. Conflict / relationship taxonomy preservation (CO-001..CO-011, descriptive only).
9. Advice comparison non-adjudication (material difference/contradiction detected, decision=None).
10. Traceability navigation methods (W5.8 helpers function end-to-end).
11. Security approval gating fail-closed (0 records returned under approved-only filter).
12. Project / tenant isolation and schema guardrails (extra="forbid").
13. Controlled failure and limitation handling (empty/whitespace queries, parameter clamping).
14. Corpus and ChromaDB immutability (15 candidate records, 0 approved, 15 vectors, unmutated hashes).
"""

import hashlib
import json
import re
from pathlib import Path
import pytest
from pydantic import ValidationError

from rag.evaluation.evaluation_dataset import EvaluationDatasetValidator
from rag.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.retrieval.retriever import RegulatoryRetriever
from rag.retrieval.vector_store import ChromaVectorStore
from rag.generation.grounded_generator import GroundedGenerator
from rag.output.structured_response import ResponseStatus, StructuredAIResponse
from rag.pipeline.advice_adapter import AdviceRAGAdapter, AdviceWorkflowStatus, AdviceRAGResult
from rag.pipeline.advice_comparator import (
    AdviceComparator,
    AdvisorAdviceItem,
    AdviceComparisonResult,
    ComparisonDifferenceType,
)
from rag.conflict.conflict_detector import ConflictDetector, ConflictType
from api.models.query import QueryRequest


@pytest.fixture(scope="module")
def dataset_validator():
    return EvaluationDatasetValidator()


@pytest.fixture(scope="module")
def benchmark_cases(dataset_validator):
    return dataset_validator.load_cases()


@pytest.fixture(scope="module")
def retrieval_evaluator():
    return RetrievalEvaluator()


@pytest.fixture(scope="module")
def grounded_generator():
    return GroundedGenerator()


@pytest.fixture(scope="module")
def advice_adapter():
    return AdviceRAGAdapter()


@pytest.fixture(scope="module")
def advice_comparator():
    return AdviceComparator()


# ==============================================================================
# 1. Retrieval Baseline Concordance (Matches W4.7 Baseline)
# ==============================================================================

def test_w59_retrieval_baseline_metrics_concordance(retrieval_evaluator, benchmark_cases):
    """Test 1: Verify current retrieval metrics against the frozen W4.7 baseline."""
    agg_metrics, case_results = retrieval_evaluator.evaluate_all(benchmark_cases, top_k=5)

    # 21 applicable benchmark cases, 13 zero-expected / safety cases
    assert agg_metrics.evaluated_cases == 21
    assert agg_metrics.zero_expected_cases == 13

    # Exact W4.7 baseline concordance to 4 decimal places
    assert agg_metrics.precision_at_k[1] == 0.9048, f"Expected P@1=0.9048, got {agg_metrics.precision_at_k[1]}"
    assert agg_metrics.recall_at_k[1] == 0.7381, f"Expected R@1=0.7381, got {agg_metrics.recall_at_k[1]}"
    assert agg_metrics.hit_rate_at_k[1] == 0.9048, f"Expected HitRate@1=0.9048, got {agg_metrics.hit_rate_at_k[1]}"
    assert agg_metrics.mrr == 0.9524, f"Expected MRR=0.9524, got {agg_metrics.mrr}"

    # Multi-depth metrics
    assert agg_metrics.precision_at_k[3] == 0.4444
    assert agg_metrics.recall_at_k[3] == 0.9762
    assert agg_metrics.hit_rate_at_k[3] == 1.0000

    assert agg_metrics.precision_at_k[5] == 0.2762
    assert agg_metrics.recall_at_k[5] == 1.0000
    assert agg_metrics.hit_rate_at_k[5] == 1.0000


# ==============================================================================
# 2. Source Grounding Fidelity
# ==============================================================================

def test_w59_source_grounding_fidelity(grounded_generator):
    """Test 2: Ensure generated responses are factual, source-grounded, and candidate-gated."""
    response: StructuredAIResponse = grounded_generator.generate_structured_response(
        query="What constitutes an offence of bribing another person under the UK Bribery Act?",
        top_k=3,
    )

    # Must be grounded with citations
    assert response.status == ResponseStatus.GROUNDED
    assert response.grounded is True
    assert len(response.citations) > 0
    assert len(response.provenance) > 0

    # External status mapped cleanly
    assert response.to_external_status() in {"SUCCESS", "CONFLICT_DETECTED"}

    # Answer text must incorporate factual regulatory context
    answer_text = response.answer.lower()
    assert "bribery" in answer_text or "offence" in answer_text or "person" in answer_text

    # Citations must strictly match retrieved chunks
    retrieved_chunk_ids = {item.chunk_id for item in response.retrieved_evidence}
    for citation in response.citations:
        assert citation.chunk_id in retrieved_chunk_ids

    # Candidate evidence metadata must be flagged since all corpus records are Candidate
    assert response.metadata.has_candidate_evidence is True
    assert response.metadata.approved_evidence_count == 0


# ==============================================================================
# 3. Citation Correctness & Metadata Authenticity
# ==============================================================================

def test_w59_citation_correctness_and_metadata(grounded_generator):
    """Test 3: Verify citation IDs, chunk IDs, and official URLs match authoritative registers."""
    response = grounded_generator.generate_structured_response(
        query="commercial organisations failure to prevent bribery guidance",
        top_k=3,
    )

    chunk_pattern = re.compile(r"^RR-(UK|EU)-\d{2}-C\d{2}$")
    for cit in response.citations:
        assert cit.citation_id.startswith("CIT-")
        assert chunk_pattern.match(cit.chunk_id)
        assert cit.official_source is not None
        # Official URLs must point to authoritative domains, not arbitrary or hallucinated web links
        assert any(
            domain in cit.official_source
            for domain in ["legislation.gov.uk", "eur-lex.europa.eu", "justice.gov.uk"]
        )
        assert cit.validation_status == "Candidate - Awaiting Approval"
        assert cit.is_approved_for_rag is False


# ==============================================================================
# 4. Provenance Lineage Integrity
# ==============================================================================

def test_w59_provenance_lineage_integrity(grounded_generator):
    """Test 4: Verify provenance records provide complete audit lineage without internal leaks."""
    response = grounded_generator.generate_structured_response(
        query="bribery offence penalties",
        top_k=2,
    )

    assert len(response.provenance) > 0
    for prov in response.provenance:
        assert prov.chunk_id.startswith("RR-")
        assert prov.record_id.startswith("RR-")
        assert prov.source_id.startswith("UK-") or prov.source_id.startswith("EU-")
        assert prov.regulation is not None
        assert prov.jurisdiction in {"UK", "EU"}
        assert prov.is_approved_for_rag is False
        assert prov.validation_status == "Candidate - Awaiting Approval"

        # Security check: zero exposure of internal database credentials or passwords
        prov_json = prov.model_dump_json()
        assert "password" not in prov_json.lower()
        assert "secret" not in prov_json.lower()
        assert "api_key" not in prov_json.lower()


# ==============================================================================
# 5. Evidence Gap Safe Disclosure
# ==============================================================================

def test_w59_evidence_gap_safe_disclosure(grounded_generator):
    """Test 5: Unrepresented provisions return safe coverage limitation without accusing user/advisor."""
    # Query specifically targeting Section 7 corporate failure to prevent bribery (CASE-02)
    response = grounded_generator.generate_structured_response(
        query="What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?",
        top_k=3,
    )

    assert response.status == ResponseStatus.INSUFFICIENT_EVIDENCE
    assert response.to_external_status() == "GAP_DETECTED"
    assert response.gap is not None
    assert response.gap.is_gap is True
    assert response.gap.coverage_nature == "CORPUS_COVERAGE_LIMITATION"
    assert "Section 7" in response.gap.user_safe_message
    assert "not represented" in response.gap.user_safe_message.lower()


# ==============================================================================
# 6. No-Source Handling
# ==============================================================================

def test_w59_no_source_handling(grounded_generator):
    """Test 6: Query with zero relevant regulatory sources returns safe handling without hallucination."""
    # Query with approved_only=True returns zero records (CASE-28 behavior)
    response = grounded_generator.generate_structured_response(
        query="commercial bribery requirements",
        filter_approved_only=True,
    )

    assert response.status == ResponseStatus.UNAPPROVED_EVIDENCE
    assert response.to_external_status() == "NO_SOURCE_FOUND"
    assert len(response.citations) == 0
    assert len(response.provenance) == 0
    assert response.metadata.approved_evidence_count == 0


# ==============================================================================
# 7. Unsupported Out-of-Corpus Question
# ==============================================================================

def test_w59_unsupported_out_of_corpus_question():
    """Test 7: Out-of-scope query (e.g. DORA / NIS2 / cybersecurity) returns OUT_OF_SCOPE."""
    from rag.generation.llm_interface import MockLLMProvider
    from rag.generation.gap_handler import GapType
    gen = GroundedGenerator(llm_provider=MockLLMProvider())
    response = gen.generate_structured_response(
        query="What cybersecurity incident reporting requirements apply under DORA and NIS2?",
        top_k=3,
    )

    assert response.status == ResponseStatus.OUT_OF_SCOPE
    assert response.to_external_status() == "GAP_DETECTED"
    assert response.gap is not None
    assert response.gap.is_gap is True
    assert response.gap.gap_type == GapType.OUT_OF_SCOPE


# ==============================================================================
# 8. Conflict / Relationship Taxonomy Preservation
# ==============================================================================

def test_w59_conflict_relationship_taxonomy_preservation(retrieval_evaluator):
    """Test 8: Co-retrieved related sources trigger canonical registered relationships descriptively."""
    detector = ConflictDetector()

    # Retrieve chunks that cover both Bribery Act 2010 (UK-01) and MoJ Guidance (UK-02)
    retriever = RegulatoryRetriever()
    chunks = retriever.retrieve("Bribery Act 2010 commercial organisations adequate procedures guidance", top_k=5)

    findings = detector.detect(chunks)
    assert len(findings) >= 1
    f = next((item for item in findings if item.conflict_id == "CO-001"), None)
    assert f is not None
    assert f.relationship == "Overlap - complementary"
    assert f.conflict_type == ConflictType.OVERLAP
    assert "No legal conflict resolution is made by this system." in f.message


# ==============================================================================
# 9. Advice Comparison Non-Adjudication
# ==============================================================================

def test_w59_advice_comparison_non_adjudication(advice_comparator):
    """Test 9: Advice comparison identifies contradictions without adjudicating a winner."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-W59-001",
        advice_text="Anti-bribery prevention procedures are mandatory and strictly required for all commercial organisations.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-W59-002",
        advice_text="Anti-bribery prevention procedures are voluntary and optional for commercial organisations.",
    )

    result: AdviceComparisonResult = advice_comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        comparison_id="CMP-W59-EVAL",
        jurisdiction="UK",
        regulatory_area="Anti-Bribery",
        top_k=5,
    )

    # Contradiction flagged
    assert any(d.is_contradiction for d in result.differences)
    # Supporting evidence assessed
    assert len(result.supporting_evidence) == 2
    # SME human review mandatory
    assert result.human_review_required is True
    # CRITICAL: Decision must remain strictly None at RAG layer
    assert result.decision is None
    # Mandatory disclaimer present
    assert "does not determine which advisor is" in result.disclaimer.lower()


# ==============================================================================
# 10. Traceability Navigation Methods
# ==============================================================================

def test_w59_traceability_navigation_methods(advice_comparator, advice_adapter):
    """Test 10: Traceability navigation helper methods return complete correlated traces."""
    # 1. Comparison traceability
    a1 = AdvisorAdviceItem(
        advice_id="ADV-W59-TR-1",
        advice_text="Under Section 1 of the UK Bribery Act 2010, bribing another person is an offence.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-W59-TR-2",
        advice_text="Commercial organisations must implement proportionate procedures under Ministry of Justice Guidance.",
    )

    cmp_res = advice_comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        comparison_id="CMP-W59-TRACE",
        request_id="REQ-W59-001",
        project_id="PRJ-W59-TRACE",
        requirement_ids=["REQ-ANTI-BRIBERY"],
        top_k=5,
    )

    summary = cmp_res.get_full_traceability_summary()
    assert summary["comparison_id"] == "CMP-W59-TRACE"
    assert summary["request_id"] == "REQ-W59-001"
    assert summary["project_id"] == "PRJ-W59-TRACE"
    assert summary["is_adjudicated"] is False

    trace_a1 = cmp_res.get_evidence_trace_for_advice("ADV-W59-TR-1")
    assert trace_a1 is not None
    assert trace_a1["advice_id"] == "ADV-W59-TR-1"

    # 2. Advice adapter traceability
    query_req = QueryRequest(
        id="REQ-W59-002",
        query="bribing another person offence",
        requirement_ids=["REQ-ANTI-BRIBERY"],
        advisor_advice_ids=["ADV-W59-TR-1"],
        context={"jurisdiction": "UK"},
    )
    adv_res = advice_adapter.execute_from_request(query_req)

    adv_trace = adv_res.get_evidence_trace()
    assert adv_trace["request_id"] == "REQ-W59-002"
    assert adv_trace["advisor_advice_ids"] == ["ADV-W59-TR-1"]
    assert len(adv_trace["citations"]) > 0


# ==============================================================================
# 11. Security Approval Gating Fail-Closed
# ==============================================================================

def test_w59_security_approval_gating_fail_closed(grounded_generator):
    """Test 11: Candidate records fail-closed under approved-only filtering."""
    retriever = RegulatoryRetriever()

    # Direct retrieval with filter_approved_only=True must return exactly 0 results
    approved_chunks = retriever.retrieve("Bribery Act 2010 Section 1", filter_approved_only=True)
    assert len(approved_chunks) == 0

    # Grounded generator with filter_approved_only=True must not return candidate citations
    res = grounded_generator.generate_structured_response(
        query="Bribery Act 2010 Section 1",
        filter_approved_only=True,
    )
    assert len(res.citations) == 0
    assert len(res.provenance) == 0
    assert res.status == ResponseStatus.UNAPPROVED_EVIDENCE
    assert res.to_external_status() == "NO_SOURCE_FOUND"


# ==============================================================================
# 12. Project / Tenant Isolation & Schema Guardrails
# ==============================================================================

def test_w59_project_tenant_isolation_and_schema_guardrails():
    """Test 12: Enforce extra='forbid' to prevent client payload bypass and enforce isolation."""
    # Extra unexpected fields must raise ValidationError
    with pytest.raises(ValidationError):
        QueryRequest(
            query="test query",
            malicious_field="bypass_authorization",  # type: ignore[call-arg]
        )

    # Valid request with project_id
    valid_req = QueryRequest(
        query="bribery offence",
        project_id="PRJ-TENANT-ALPHA",
        requirement_ids=["REQ-001"],
    )
    assert valid_req.project_id == "PRJ-TENANT-ALPHA"
    assert valid_req.requirement_ids == ["REQ-001"]


# ==============================================================================
# 13. Controlled Failure & Limitation Handling
# ==============================================================================

def test_w59_controlled_failure_and_limitation_handling(grounded_generator):
    """Test 13: Empty queries, whitespace queries, and out-of-range parameters handle safely."""
    # Empty query raises ValidationError in QueryRequest model
    with pytest.raises(ValidationError):
        QueryRequest(query="")

    with pytest.raises(ValidationError):
        QueryRequest(query="   ")

    # Top-k clamping in retriever
    retriever = RegulatoryRetriever()
    clamped_res = retriever.retrieve("bribery", top_k=100)
    # Corpus has exactly 15 records total, so retrieval cannot return more than 15
    assert len(clamped_res) <= 15


# ==============================================================================
# 14. Corpus & ChromaDB Immutability
# ==============================================================================

def test_w59_corpus_and_chromadb_immutability():
    """Test 14: Canonical JSON hashes, 15 Candidate / 0 Approved state, and 15 Chroma vectors are unmutated."""
    records_path = Path("data/processed/normalized_regulatory_records.json")
    chunks_path = Path("data/processed/regulatory_chunks.json")

    assert records_path.exists()
    assert chunks_path.exists()

    # Exact frozen SHA256 hashes
    records_hash = hashlib.sha256(records_path.read_bytes()).hexdigest()
    chunks_hash = hashlib.sha256(chunks_path.read_bytes()).hexdigest()

    assert records_hash == "5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d"
    assert chunks_hash == "05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef"

    # Verify 15 Candidate / 0 Approved
    records_data = json.loads(records_path.read_text(encoding="utf-8"))
    assert len(records_data) == 15
    assert all(r.get("validation_status") == "Candidate - Awaiting Approval" for r in records_data)
    assert all(r.get("is_approved_for_rag") is False for r in records_data)

    # Verify ChromaDB contains exactly 15 vectors
    store = ChromaVectorStore()
    assert store._get_collection().count() == 15
