"""Automated test suite for Week 5 — Task W5.8: Regulatory <-> Advice Traceability.

Validates the complete RAG-side Regulatory -> Advice traceability chain:
Regulatory Record -> Regulatory Chunk -> RAG Retrieval -> Evidence -> Citation ->
Provenance -> Advice / Advisor -> Comparison -> Conflict / Gap -> Human Review.

Ensures that every finding, comparison stance, conflict, and evidence gap can answer:
"Why did RAG produce this finding for this advice?" and trace back to the exact
regulatory evidence used by the RAG system without asserting legal correctness.

24 Verification Scenarios:
1. Regulatory record -> chunk mapping.
2. Chunk -> source mapping.
3. Retrieved evidence -> citation mapping.
4. Citation -> provenance mapping.
5. Request ID preservation.
6. Project ID preservation where supported.
7. Requirement IDs preservation.
8. Advisor 1 ID preservation.
9. Advisor 2 ID preservation.
10. Comparison ID preservation.
11. Comparison -> evidence traceability (supporting_chunk_ids linked to citations/provenance).
12. Conflict -> regulatory evidence traceability (retrieved_chunk_ids linked to citations/provenance).
13. Evidence gap -> safe traceability (coverage_nature without blaming advisor).
14. Approval state preserved (is_approved_for_rag and validation_status).
15. Candidate evidence remains fail-closed (filter_approved_only=True yields 0).
16. Zero fabricated citations (citations only reference retrieved chunks).
17. Zero fabricated provenance (provenance only references retrieved chunks).
18. Project isolation enforced without cross-tenant evidence leakage.
19. W5.4 AdviceRAGAdapter compatibility and get_evidence_trace().
20. W5.5 AdviceComparator compatibility and get_evidence_trace_for_advice().
21. W5.6 Conflict/Relationship compatibility and get_conflict_trace().
22. W5.7 Regulatory <-> RAG boundary compatibility (zero corpus mutations).
23. W4.11 response wire compatibility.
24. Complete end-to-end trace verification from Advice to Regulatory Record.
"""

import json
from pathlib import Path
import pytest

from rag.ingestion.schemas import NormalizedRegulatoryRecord, RegulatoryChunk
from rag.ingestion.chunker import RegulatoryRecordChunker
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.retrieval.vector_store import ChromaVectorStore
from rag.generation.citations import CitationBuilder, Citation, ProvenanceRecord
from rag.generation.gap_handler import GapHandler, GapType
from rag.generation.grounded_generator import GroundedGenerator
from rag.pipeline.advice_adapter import AdviceRAGAdapter, AdviceWorkflowStatus
from rag.pipeline.advice_comparator import (
    AdviceComparator,
    AdvisorAdviceItem,
    AdviceComparisonRequest,
    AdviceComparisonResult,
    ComparisonDifferenceType,
)
from rag.conflict.conflict_detector import ConflictDetector, ConflictFinding
from rag.output.structured_response import StructuredAIResponse, ResponseStatus


DATA_DIR = Path("data")
NORMALIZED_RECORDS_PATH = DATA_DIR / "processed" / "normalized_regulatory_records.json"
CHUNKS_PATH = DATA_DIR / "processed" / "regulatory_chunks.json"


@pytest.fixture(scope="module")
def retriever():
    """Shared RegulatoryRetriever instance."""
    return RegulatoryRetriever()


@pytest.fixture(scope="module")
def generator():
    """Shared GroundedGenerator instance."""
    return GroundedGenerator()


@pytest.fixture(scope="module")
def adapter():
    """Shared AdviceRAGAdapter instance."""
    return AdviceRAGAdapter()


@pytest.fixture(scope="module")
def comparator():
    """Shared AdviceComparator instance."""
    return AdviceComparator()


# ==============================================================================
# 1. Regulatory record -> chunk mapping
# ==============================================================================
def test_w58_record_to_chunk_mapping():
    """Test 1: Record ID, index, and total chunk count map deterministically to chunk."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-TRC",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Offences of bribing another person",
        requirement="General bribery offences requirement.",
        validation_status="Candidate - Awaiting Approval",
    )
    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_record(rec)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.record_id == "RR-TEST-TRC"
    assert c.source_id == "UK-01"
    assert c.chunk_id == "RR-TEST-TRC-C01"
    assert c.chunk_index == 0
    assert c.total_chunks == 1


# ==============================================================================
# 2. Chunk -> source mapping
# ==============================================================================
def test_w58_chunk_to_source_mapping(retriever):
    """Test 2: Retrieved chunk maps deterministically to parent source register ID."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=2)
    assert len(results) >= 1
    for chunk in results:
        assert chunk.chunk_id.startswith(f"{chunk.record_id}-")
        assert chunk.source_id.startswith("UK-") or chunk.source_id.startswith("EU-")


# ==============================================================================
# 3. Retrieved evidence -> citation mapping
# ==============================================================================
def test_w58_retrieved_evidence_to_citation_mapping(retriever):
    """Test 3: Citation model maps deterministically from retrieved chunk attributes."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    chunk = results[0]
    citations, _ = CitationBuilder.build_citations([chunk], is_grounded=True)
    assert len(citations) == 1
    cit = citations[0]
    assert cit.citation_id == f"CIT-{chunk.chunk_id}"
    assert cit.chunk_id == chunk.chunk_id
    assert cit.record_id == chunk.record_id
    assert cit.source_id == chunk.source_id
    assert cit.regulation == chunk.regulation
    assert cit.section_article == chunk.section_article
    assert cit.formatted_citation == f"[{chunk.chunk_id} | {chunk.record_id} | {chunk.regulation} | {chunk.section_article}]"


# ==============================================================================
# 4. Citation -> provenance mapping
# ==============================================================================
def test_w58_citation_to_provenance_mapping(retriever):
    """Test 4: Provenance record derives directly and faithfully from citation."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    citations, provenance = CitationBuilder.build_citations(results, is_grounded=True)
    assert len(citations) == 1
    assert len(provenance) == 1
    c = citations[0]
    p = provenance[0]
    assert p.chunk_id == c.chunk_id
    assert p.record_id == c.record_id
    assert p.source_id == c.source_id
    assert p.regulation == c.regulation
    assert p.section_article == c.section_article
    assert p.validation_status == c.validation_status
    assert p.is_approved_for_rag == c.is_approved_for_rag


# ==============================================================================
# 5. Request ID preservation
# ==============================================================================
def test_w58_request_id_preservation(adapter, comparator):
    """Test 5: Request ID is preserved across Advice RAG execution and Advice comparison."""
    # Adapter execution
    res_adapter = adapter.execute_advice_rag(
        query="What constitutes an offence under Section 1?",
        request_id="REQ-TEST-W58-ADAPTER",
    )
    assert res_adapter.traceability.request_id == "REQ-TEST-W58-ADAPTER"

    # Comparator execution
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Advice 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Advice 2")
    res_cmp = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        request_id="REQ-TEST-W58-COMPARE",
    )
    assert res_cmp.traceability.request_id == "REQ-TEST-W58-COMPARE"


# ==============================================================================
# 6. Project ID preservation
# ==============================================================================
def test_w58_project_id_preservation(adapter, comparator):
    """Test 6: Project ID is preserved cleanly in traceability metadata."""
    res_adapter = adapter.execute_advice_rag(
        query="Section 1 bribery offence",
        project_id="PRJ-WORKSPACE-42",
    )
    assert res_adapter.traceability.project_id == "PRJ-WORKSPACE-42"

    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Advice 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Advice 2")
    res_cmp = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        project_id="PRJ-WORKSPACE-42",
    )
    assert res_cmp.traceability.project_id == "PRJ-WORKSPACE-42"


# ==============================================================================
# 7. Requirement IDs preservation
# ==============================================================================
def test_w58_requirement_ids_preservation(adapter, comparator):
    """Test 7: Requirement IDs pass through without alteration or loss."""
    req_ids = ["REQ-FIN-01", "REQ-FIN-02"]
    res_adapter = adapter.execute_advice_rag(
        query="Section 1 bribery offence",
        requirement_ids=req_ids,
    )
    assert res_adapter.traceability.requirement_ids == req_ids

    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Advice 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Advice 2")
    res_cmp = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        requirement_ids=req_ids,
    )
    assert res_cmp.traceability.requirement_ids == req_ids


# ==============================================================================
# 8. Advisor 1 ID preservation
# ==============================================================================
def test_w58_advisor_1_id_preservation(comparator):
    """Test 8: Advisor 1 ID is preserved across comparison traceability."""
    a1 = AdvisorAdviceItem(advice_id="ADV-LEGAL-A", advice_text="First stance")
    a2 = AdvisorAdviceItem(advice_id="ADV-LEGAL-B", advice_text="Second stance")
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2)
    assert res.traceability.advisor_1_id == "ADV-LEGAL-A"
    assert res.advisor_1.advice_id == "ADV-LEGAL-A"


# ==============================================================================
# 9. Advisor 2 ID preservation
# ==============================================================================
def test_w58_advisor_2_id_preservation(comparator):
    """Test 9: Advisor 2 ID is preserved across comparison traceability."""
    a1 = AdvisorAdviceItem(advice_id="ADV-LEGAL-A", advice_text="First stance")
    a2 = AdvisorAdviceItem(advice_id="ADV-LEGAL-B", advice_text="Second stance")
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2)
    assert res.traceability.advisor_2_id == "ADV-LEGAL-B"
    assert res.advisor_2.advice_id == "ADV-LEGAL-B"


# ==============================================================================
# 10. Comparison ID preservation
# ==============================================================================
def test_w58_comparison_id_preservation(comparator):
    """Test 10: Comparison ID is preserved identically in result and traceability."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Advice 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Advice 2")
    res = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        comparison_id="CMP-CORRELATION-999",
    )
    assert res.comparison_id == "CMP-CORRELATION-999"
    assert res.traceability.comparison_id == "CMP-CORRELATION-999"


# ==============================================================================
# 11. Comparison -> evidence traceability
# ==============================================================================
def test_w58_comparison_to_evidence_traceability(comparator):
    """Test 11: get_evidence_trace_for_advice() maps advice ID to supporting chunks, citations, and provenance."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    )
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    trace_1 = res.get_evidence_trace_for_advice("ADV-001")
    assert trace_1 is not None
    assert trace_1["advice_id"] == "ADV-001"
    assert len(trace_1["supporting_chunk_ids"]) >= 1
    assert len(trace_1["citations"]) >= 1
    assert len(trace_1["provenance"]) >= 1

    # Verify that citations in the trace correspond to the supporting chunk IDs
    for cit in trace_1["citations"]:
        assert cit.chunk_id in trace_1["supporting_chunk_ids"]


# ==============================================================================
# 12. Conflict -> regulatory evidence traceability
# ==============================================================================
def test_w58_conflict_to_regulatory_evidence_traceability(comparator):
    """Test 12: get_conflict_trace() maps conflict ID to supporting chunks, citations, and provenance."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    )
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert len(res.relationships) >= 1
    rel = res.relationships[0]
    conflict_trace = res.get_conflict_trace(rel.conflict_id)
    assert conflict_trace is not None
    assert conflict_trace["conflict_id"] == "CO-001"
    assert conflict_trace["source_id_1"] == "UK-01"
    assert conflict_trace["source_id_2"] == "UK-02"
    assert len(conflict_trace["retrieved_chunk_ids"]) >= 2
    assert len(conflict_trace["citations"]) >= 1


# ==============================================================================
# 13. Evidence gap -> safe traceability
# ==============================================================================
def test_w58_evidence_gap_safe_traceability(comparator):
    """Test 13: Evidence gap explains corpus limitation without asserting advisor is false."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Section 7 Failure of commercial organisations to prevent bribery is a strict liability offense.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Section 7 Failure of commercial organisations provides an adequate procedures defense.",
    )
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2)

    assert len(res.evidence_gaps) >= 1
    gap = res.evidence_gaps[0]
    assert gap.is_gap is True
    assert gap.coverage_nature in {"CORPUS_COVERAGE_LIMITATION", "RETRIEVAL_LIMITATION"}
    assert "limitations" in gap.user_safe_message.lower() or "not represented" in gap.user_safe_message.lower()


# ==============================================================================
# 14. Approval state preserved
# ==============================================================================
def test_w58_approval_state_preserved(comparator):
    """Test 14: Traceability preserves validation_status and is_approved_for_rag across all records."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Bribery Act 2010 Section 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Bribery Act Guidance")
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=2)

    for prov in res.provenance:
        assert prov.validation_status == "Candidate - Awaiting Approval"
        assert prov.is_approved_for_rag is False


# ==============================================================================
# 15. Candidate evidence remains fail-closed
# ==============================================================================
def test_w58_candidate_evidence_remains_fail_closed(comparator):
    """Test 15: filter_approved_only=True returns 0 chunks and 0 citations fail-closed."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Bribery Act 2010 Section 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Bribery Act Guidance")
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2, filter_approved_only=True)

    assert len(res.citations) == 0
    assert len(res.provenance) == 0
    assert len(res.relationships) == 0
    assert res.human_review_required is True


# ==============================================================================
# 16. Zero fabricated citations
# ==============================================================================
def test_w58_zero_fabricated_citations(retriever):
    """Test 16: Citations strictly reference retrieved evidence chunks; non-retrieved chunks produce zero citations."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    citations, _ = CitationBuilder.build_citations(results, is_grounded=True)
    retrieved_chunk_ids = {r.chunk_id for r in results}
    for cit in citations:
        assert cit.chunk_id in retrieved_chunk_ids


# ==============================================================================
# 17. Zero fabricated provenance
# ==============================================================================
def test_w58_zero_fabricated_provenance(retriever):
    """Test 17: Provenance records strictly reference retrieved evidence chunks."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    _, provenance = CitationBuilder.build_citations(results, is_grounded=True)
    retrieved_chunk_ids = {r.chunk_id for r in results}
    for prov in provenance:
        assert prov.chunk_id in retrieved_chunk_ids


# ==============================================================================
# 18. Project isolation enforced
# ==============================================================================
def test_w58_project_isolation_enforced(retriever):
    """Test 18: Passing tenant project ID isolates vectors; zero cross-project vector leakage."""
    res_tenant_a = retriever.retrieve("Bribery Act", project_id="TENANT-A")
    res_tenant_b = retriever.retrieve("Bribery Act", project_id="TENANT-B")
    assert len(res_tenant_a) == 0
    assert len(res_tenant_b) == 0


# ==============================================================================
# 19. W5.4 AdviceRAGAdapter compatibility and get_evidence_trace()
# ==============================================================================
def test_w58_adapter_compatibility_and_trace(adapter):
    """Test 19: AdviceRAGAdapter produces valid result with working get_evidence_trace()."""
    res = adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person under Section 1?",
        request_id="REQ-TEST-W58-ADP",
        requirement_ids=["REQ-01"],
        advisor_advice_ids=["ADV-NOTE-01"],
        top_k=1,
    )
    trace = res.get_evidence_trace()
    assert trace["request_id"] == "REQ-TEST-W58-ADP"
    assert trace["requirement_ids"] == ["REQ-01"]
    assert trace["advisor_advice_ids"] == ["ADV-NOTE-01"]
    assert len(trace["citations"]) >= 1
    assert len(trace["provenance"]) >= 1


# ==============================================================================
# 20. W5.5 AdviceComparator compatibility and get_evidence_trace_for_advice()
# ==============================================================================
def test_w58_comparator_compatibility_and_trace(comparator):
    """Test 20: AdviceComparator produces valid comparison with working get_evidence_trace_for_advice()."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Bribery Act 2010 Section 1")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Bribery Act Guidance Ministry of Justice")
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=2)

    assert res.decision is None
    trace = res.get_evidence_trace_for_advice("ADV-001")
    assert trace is not None
    assert trace["advice_id"] == "ADV-001"


# ==============================================================================
# 21. W5.6 Conflict/Relationship compatibility and get_conflict_trace()
# ==============================================================================
def test_w58_conflict_compatibility_and_trace(comparator):
    """Test 21: AdviceComparator preserves registered relationships with working get_conflict_trace()."""
    a1 = AdvisorAdviceItem(advice_id="ADV-001", advice_text="Bribery Act 2010 Section 1 general offences")
    a2 = AdvisorAdviceItem(advice_id="ADV-002", advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles")
    res = comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert len(res.relationships) >= 1
    rel = res.relationships[0]
    trace = res.get_conflict_trace(rel.conflict_id)
    assert trace is not None
    assert trace["conflict_id"] == "CO-001"


# ==============================================================================
# 22. W5.7 Regulatory <-> RAG boundary compatibility
# ==============================================================================
def test_w58_regulatory_boundary_compatibility(retriever):
    """Test 22: Canonical JSON records on disk remain unchanged after traceability queries."""
    with open(NORMALIZED_RECORDS_PATH, "r", encoding="utf-8") as f:
        recs_before = json.load(f)

    retriever.retrieve("Bribery Act 2010 Section 1", top_k=5)

    with open(NORMALIZED_RECORDS_PATH, "r", encoding="utf-8") as f:
        recs_after = json.load(f)

    assert recs_before == recs_after


# ==============================================================================
# 23. W4.11 response wire compatibility
# ==============================================================================
def test_w58_w411_wire_compatibility(generator):
    """Test 23: GroundedGenerator output satisfies the locked W4.11 StructuredAIResponse contract."""
    resp = generator.generate_structured_response("Bribery Act 2010 Section 1", top_k=1)
    assert isinstance(resp, StructuredAIResponse)
    assert resp.grounded is True
    assert len(resp.citations) >= 1
    assert len(resp.provenance) >= 1
    assert resp.to_external_status() == "SUCCESS"


# ==============================================================================
# 24. Complete end-to-end trace verification
# ==============================================================================
def test_w58_complete_end_to_end_trace(comparator):
    """Test 24: Verifies the entire end-to-end chain from advice IDs to regulatory record and provenance."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-E2E-001",
        advice_text="Under Section 1 of the Bribery Act 2010, bribing another person is a statutory offence.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-E2E-002",
        advice_text="Commercial organisations must implement proportionate procedures under Ministry of Justice Guidance.",
    )

    res: AdviceComparisonResult = comparator.compare_advice(
        advisor_1=a1,
        advisor_2=a2,
        comparison_id="CMP-E2E-TRACE",
        request_id="REQ-E2E-CORRELATION",
        requirement_ids=["REQ-CORP-GOV-01"],
        jurisdiction="UK",
        regulatory_area="Anti-Bribery",
        top_k=5,
    )

    # 1. Comparison & Traceability Context
    summary = res.get_full_traceability_summary()
    assert summary["comparison_id"] == "CMP-E2E-TRACE"
    assert summary["request_id"] == "REQ-E2E-CORRELATION"
    assert summary["requirement_ids"] == ["REQ-CORP-GOV-01"]
    assert summary["advisor_1_id"] == "ADV-E2E-001"
    assert summary["advisor_2_id"] == "ADV-E2E-002"
    assert summary["is_adjudicated"] is False
    assert summary["decision"] is None

    # 2. Advisor 1 Evidence Trace
    adv_1_trace = summary["advisor_1_evidence"]
    assert adv_1_trace is not None
    assert adv_1_trace["evidence_status"] in {"SUPPORTED", "PARTIALLY_SUPPORTED"}
    assert "RR-UK-01-C01" in adv_1_trace["supporting_chunk_ids"]
    assert "UK-01" in adv_1_trace["supporting_source_ids"]

    # 3. Citation and Provenance Trace
    cit = adv_1_trace["citations"][0]
    assert cit.chunk_id == "RR-UK-01-C01"
    assert cit.record_id == "RR-UK-01"
    assert cit.source_id == "UK-01"
    assert cit.regulation == "Bribery Act 2010"
    assert cit.section_article == "Section 1"
    assert "https://www.legislation.gov.uk" in cit.official_source

    prov = adv_1_trace["provenance"][0]
    assert prov.record_id == "RR-UK-01"
    assert prov.validation_status == "Candidate - Awaiting Approval"
    assert prov.is_approved_for_rag is False

    # 4. Conflict Trace
    assert summary["conflict_count"] >= 1
    co_trace = res.get_conflict_trace("CO-001")
    assert co_trace is not None
    assert co_trace["source_id_1"] == "UK-01"
    assert co_trace["source_id_2"] == "UK-02"

    # 5. Non-Adjudication Invariant
    assert res.human_review_required is True
    assert res.decision is None
    assert "does NOT determine which advisor is legally or professionally correct" in res.disclaimer
