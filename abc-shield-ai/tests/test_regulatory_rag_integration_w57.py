"""Automated test suite for Week 5 — Task W5.7: Regulatory <-> RAG Integration.

Validates the clean integration boundary between:
- Madhesh's Regulatory Data / Knowledge Layer (source files, normalization, approval governance)
- Padma's RAG Layer (retrieval, grounding, citations, provenance, gaps, conflicts, advice comparison)

20 Verification Scenarios:
1. Regulatory record metadata reaches RAG chunks (NormalizedRegulatoryRecord -> RegulatoryChunk).
2. record_id preserved across record, chunk, ChromaDB, retrieval result, citation, and provenance.
3. source_id preserved across record, chunk, ChromaDB, retrieval result, citation, and provenance.
4. chunk_id preserved across chunk, ChromaDB, retrieval result, citation, and provenance.
5. chunk_index and total_chunks preserved from chunk to ChromaDB metadata.
6. Approval state (is_approved_for_rag) preserved across record, chunk, ChromaDB, retrieval, and provenance.
7. Candidate records remain fail-closed (15 Candidate / 0 Approved).
8. Approved-only retrieval returns zero records currently due to 0 approved records.
9. Jurisdiction filtering correctly restricts chunks (UK vs EU).
10. Project/tenant isolation correctly isolates tenant context.
11. Retrieved evidence contains sufficient source metadata for display and audit.
12. Citation traces back to the regulatory source with formatted citation.
13. Provenance traces back to the regulatory source with complete audit lineage.
14. Evidence-gap behavior remains safe and non-prejudicial.
15. AdviceRAGAdapter (W5.4) remains compatible with Regulatory <-> RAG boundary.
16. AdviceComparator (W5.5) remains compatible with Regulatory <-> RAG boundary.
17. W5.6 conflict/relationship integration remains compatible.
18. No regulatory record is mutated by RAG operations.
19. No approval state is mutated by RAG operations.
20. W4.11 response contract remains fully compatible.
"""

import json
from pathlib import Path
import pytest

from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    RegulatoryChunk,
    is_sme_approved,
)
from rag.ingestion.chunker import RegulatoryRecordChunker
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.retrieval.vector_store import ChromaVectorStore
from rag.generation.citations import CitationBuilder, Citation, ProvenanceRecord
from rag.generation.gap_handler import GapHandler, GapType
from rag.generation.grounded_generator import GroundedGenerator
from rag.pipeline.advice_adapter import AdviceRAGAdapter, AdviceWorkflowStatus
from rag.pipeline.advice_comparator import AdviceComparator, AdvisorAdviceItem
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
def vector_store():
    """Shared ChromaVectorStore instance."""
    return ChromaVectorStore()


@pytest.fixture(scope="module")
def generator():
    """Shared GroundedGenerator instance."""
    return GroundedGenerator()


@pytest.fixture(scope="module")
def advice_adapter():
    """Shared AdviceRAGAdapter instance."""
    return AdviceRAGAdapter()


@pytest.fixture(scope="module")
def advice_comparator():
    """Shared AdviceComparator instance."""
    return AdviceComparator()


# ==============================================================================
# 1. Regulatory record metadata reaches RAG chunks
# ==============================================================================
def test_w57_record_metadata_reaches_chunks():
    """Test 1: Chunking a NormalizedRegulatoryRecord preserves 100% of regulatory metadata."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-01",
        source_id="TEST-01",
        regulation="Test Regulation 2026",
        regulator="Test Authority",
        jurisdiction="UK",
        section_article="Section 99",
        title="Test Requirements Header",
        requirement="Firms must establish robust test controls.",
        topic="Compliance Testing",
        official_source="https://example.gov.uk/test",
        version_date="2026-01-01",
        effective_date="2026-01-01",
        validation_status="Candidate - Awaiting Approval",
        authority_level="A",
        source_type="Primary Legislation",
    )
    chunker = RegulatoryRecordChunker()
    chunks = chunker.chunk_record(rec)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.record_id == "RR-TEST-01"
    assert chunk.source_id == "TEST-01"
    assert chunk.regulation == "Test Regulation 2026"
    assert chunk.regulator == "Test Authority"
    assert chunk.jurisdiction == "UK"
    assert chunk.section_article == "Section 99"
    assert chunk.title == "Test Requirements Header"
    assert chunk.topic == "Compliance Testing"
    assert chunk.official_source == "https://example.gov.uk/test"
    assert chunk.version_date == "2026-01-01"
    assert chunk.effective_date == "2026-01-01"
    assert chunk.validation_status == "Candidate - Awaiting Approval"
    assert chunk.is_approved_for_rag is False
    assert chunk.authority_level == "A"
    assert chunk.source_type == "Primary Legislation"


# ==============================================================================
# 2. record_id preserved across pipeline
# ==============================================================================
def test_w57_record_id_preserved_across_pipeline(retriever):
    """Test 2: record_id is preserved from vector store through retrieval and citation."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    assert len(results) >= 1
    c = results[0]
    assert c.record_id.startswith("RR-")

    citations, provenance = CitationBuilder.build_citations([c], is_grounded=True)
    assert citations[0].record_id == c.record_id
    assert provenance[0].record_id == c.record_id


# ==============================================================================
# 3. source_id preserved across pipeline
# ==============================================================================
def test_w57_source_id_preserved_across_pipeline(retriever):
    """Test 3: source_id is preserved from vector store through retrieval, citation, and provenance."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    assert len(results) >= 1
    c = results[0]
    assert c.source_id in {"UK-01", "UK-02"}

    citations, provenance = CitationBuilder.build_citations([c], is_grounded=True)
    assert citations[0].source_id == c.source_id
    assert provenance[0].source_id == c.source_id


# ==============================================================================
# 4. chunk_id preserved across pipeline
# ==============================================================================
def test_w57_chunk_id_preserved_across_pipeline(retriever):
    """Test 4: chunk_id is preserved identically from vector store to citation and provenance."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    assert len(results) >= 1
    c = results[0]
    assert c.chunk_id.endswith("-C01")

    citations, provenance = CitationBuilder.build_citations([c], is_grounded=True)
    assert citations[0].chunk_id == c.chunk_id
    assert provenance[0].chunk_id == c.chunk_id
    assert citations[0].citation_id == f"CIT-{c.chunk_id}"


# ==============================================================================
# 5. chunk_index and total_chunks preserved
# ==============================================================================
def test_w57_chunk_index_and_total_chunks_preserved(vector_store):
    """Test 5: ChromaDB metadata preserves chunk_index and total_chunks."""
    collection = vector_store._get_collection()
    res = collection.get(ids=["RR-UK-01-C01"])
    meta = res["metadatas"][0]
    assert "chunk_index" in meta
    assert "total_chunks" in meta
    assert meta["chunk_index"] == 0
    assert meta["total_chunks"] == 1


# ==============================================================================
# 6. Approval state (is_approved_for_rag) preserved
# ==============================================================================
def test_w57_approval_state_preserved(retriever):
    """Test 6: is_approved_for_rag status from regulatory data is preserved in retrieval and provenance."""
    results = retriever.retrieve("Bribery Act", top_k=3)
    assert len(results) >= 1
    for c in results:
        assert c.is_approved_for_rag is False
        assert c.validation_status == "Candidate - Awaiting Approval"

    citations, provenance = CitationBuilder.build_citations(results, is_grounded=True)
    for p in provenance:
        assert p.is_approved_for_rag is False
        assert p.validation_status == "Candidate - Awaiting Approval"


# ==============================================================================
# 7. Candidate records remain fail-closed
# ==============================================================================
def test_w57_candidate_records_remain_fail_closed():
    """Test 7: Canonical files contain exactly 15 records, 100% Candidate - Awaiting Approval, 0 Approved."""
    with open(NORMALIZED_RECORDS_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 15

    for r in records:
        assert r["validation_status"] == "Candidate - Awaiting Approval"
        assert r["is_approved_for_rag"] is False
        assert is_sme_approved(r["validation_status"]) is False


# ==============================================================================
# 8. Approved-only retrieval returns zero
# ==============================================================================
def test_w57_approved_only_retrieval_returns_zero(retriever):
    """Test 8: Approved-only retrieval (filter_approved_only=True) returns exactly 0 chunks."""
    results = retriever.retrieve("Bribery Act 2010 offences", top_k=5, filter_approved_only=True)
    assert len(results) == 0


# ==============================================================================
# 9. Jurisdiction filtering remains correct
# ==============================================================================
def test_w57_jurisdiction_filtering_remains_correct(retriever):
    """Test 9: Jurisdiction filtering strictly partitions UK vs EU regulatory chunks."""
    uk_results = retriever.retrieve("anti-bribery prevention procedures", top_k=5, jurisdiction="UK")
    for r in uk_results:
        assert r.jurisdiction == "UK"
        assert r.source_id.startswith("UK-")

    eu_results = retriever.retrieve("anti-money laundering directive", top_k=5, jurisdiction="EU")
    for r in eu_results:
        assert r.jurisdiction == "EU"
        assert r.source_id.startswith("EU-")


# ==============================================================================
# 10. Project/tenant isolation remains correct
# ==============================================================================
def test_w57_project_tenant_isolation_remains_correct(retriever):
    """Test 10: Filtering by a tenant project_id isolates results from other tenants and unassigned data."""
    results = retriever.retrieve("Bribery Act", top_k=5, project_id="PRJ-TENANT-ALPHA")
    # Canonical public chunks do not belong to PRJ-TENANT-ALPHA, so 0 are returned
    assert len(results) == 0


# ==============================================================================
# 11. Retrieved evidence contains sufficient source metadata
# ==============================================================================
def test_w57_retrieved_evidence_contains_sufficient_metadata(retriever):
    """Test 11: RetrievalResult objects contain all essential metadata for frontend display and audit."""
    results = retriever.retrieve("Bribery Act 2010", top_k=1)
    assert len(results) >= 1
    c = results[0]
    assert c.regulation
    assert c.regulator
    assert c.jurisdiction
    assert c.section_article
    assert c.title
    assert c.topic
    assert c.official_source
    assert c.version_date
    assert c.effective_date
    assert c.authority_level
    assert c.source_type


# ==============================================================================
# 12. Citation traces back to the regulatory source
# ==============================================================================
def test_w57_citation_traces_to_regulatory_source(retriever):
    """Test 12: Citation model carries formatted citation string and valid official source pointer."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    citations, _ = CitationBuilder.build_citations(results, is_grounded=True)
    assert len(citations) >= 1
    cit = citations[0]
    assert cit.formatted_citation.startswith("[RR-")
    assert cit.official_source.startswith("http")
    assert cit.source_id in {"UK-01", "UK-02"}


# ==============================================================================
# 13. Provenance traces back to the regulatory source
# ==============================================================================
def test_w57_provenance_traces_to_regulatory_source(retriever):
    """Test 13: ProvenanceRecord contains full audit lineage back to regulatory record ID and source ID."""
    results = retriever.retrieve("Bribery Act 2010 Section 1", top_k=1)
    _, provenance = CitationBuilder.build_citations(results, is_grounded=True)
    assert len(provenance) >= 1
    prov = provenance[0]
    assert prov.record_id.startswith("RR-")
    assert prov.source_id.startswith("UK-")
    assert prov.validation_status == "Candidate - Awaiting Approval"
    assert prov.is_approved_for_rag is False


# ==============================================================================
# 14. Evidence-gap behavior remains safe
# ==============================================================================
def test_w57_evidence_gap_behavior_remains_safe():
    """Test 14: Querying an unrepresented provision produces a safe GapResult without legal condemnation."""
    gap = GapHandler.analyze_gap(
        query="Section 7 Failure of commercial organisations to prevent bribery",
        retrieved_chunks=[],
        is_grounded=False,
        filter_approved_only=False,
    )
    assert gap.is_gap is True
    assert gap.gap_type == GapType.NO_RETRIEVED_EVIDENCE
    assert "not contain sufficient" in gap.user_safe_message.lower()
    assert gap.coverage_nature == "RETRIEVAL_LIMITATION"


# ==============================================================================
# 15. AdviceRAGAdapter remains compatible
# ==============================================================================
def test_w57_advice_adapter_remains_compatible(advice_adapter):
    """Test 15: AdviceRAGAdapter executes grounded query against regulatory chunks and preserves citations."""
    result = advice_adapter.execute_advice_rag(
        query="What constitutes an offence of bribing another person under Section 1?",
        top_k=1,
    )
    assert result.external_status == "SUCCESS"
    assert result.workflow_status == AdviceWorkflowStatus.RAG_SUPPORTED
    assert len(result.citations) >= 1
    assert result.traceability.request_id is not None


# ==============================================================================
# 16. AdviceComparator remains compatible
# ==============================================================================
def test_w57_advice_comparator_remains_compatible(advice_comparator):
    """Test 16: AdviceComparator executes comparison against regulatory evidence and maintains decision=None."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Commercial organisations must implement anti-bribery procedures.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Commercial organisations must establish proportionate prevention procedures.",
    )
    result = advice_comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=2)

    assert result.decision is None
    assert result.human_review_required is True
    assert len(result.citations) >= 1
    assert len(result.provenance) >= 1


# ==============================================================================
# 17. W5.6 conflict/relationship integration remains compatible
# ==============================================================================
def test_w57_conflict_relationship_integration_remains_compatible(advice_comparator):
    """Test 17: Co-retrieving documented regulatory sources (UK-01 and UK-02) surfaces registered CO-001 relationship."""
    a1 = AdvisorAdviceItem(
        advice_id="ADV-001",
        advice_text="Bribery Act 2010 Section 1 offences of bribing another person.",
    )
    a2 = AdvisorAdviceItem(
        advice_id="ADV-002",
        advice_text="Bribery Act 2010 Guidance Ministry of Justice Six Principles prevention procedures.",
    )
    result = advice_comparator.compare_advice(advisor_1=a1, advisor_2=a2, top_k=5)

    assert len(result.relationships) >= 1
    rel = result.relationships[0]
    assert rel.conflict_id == "CO-001"
    assert rel.source_id_1 == "UK-01"
    assert rel.source_id_2 == "UK-02"
    assert "No legal conflict resolution is made by this system." in rel.message


# ==============================================================================
# 18. No regulatory record is mutated by RAG
# ==============================================================================
def test_w57_no_regulatory_record_mutated_by_rag(retriever, generator):
    """Test 18: Executing RAG queries does not mutate canonical JSON files on disk."""
    with open(NORMALIZED_RECORDS_PATH, "r", encoding="utf-8") as f:
        before_records = json.load(f)

    # Execute retrieval and generation
    retriever.retrieve("Bribery Act 2010 Section 1", top_k=5)
    generator.generate_structured_response("Bribery Act 2010 Section 1", top_k=2)

    with open(NORMALIZED_RECORDS_PATH, "r", encoding="utf-8") as f:
        after_records = json.load(f)

    assert before_records == after_records


# ==============================================================================
# 19. No approval state is mutated by RAG
# ==============================================================================
def test_w57_no_approval_state_mutated_by_rag(retriever, generator, advice_comparator):
    """Test 19: RAG operations never elevate Candidate records to Approved in memory or on disk."""
    chunks = retriever.retrieve("Bribery Act 2010 Section 1", top_k=5)
    for c in chunks:
        assert c.is_approved_for_rag is False
        assert c.validation_status == "Candidate - Awaiting Approval"

    resp = generator.generate_structured_response("Bribery Act 2010", top_k=2)
    assert resp.metadata.approved_evidence_count == 0
    assert resp.metadata.has_candidate_evidence is True

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        disk_chunks = json.load(f)
    for c in disk_chunks:
        assert c["is_approved_for_rag"] is False
        assert c["validation_status"] == "Candidate - Awaiting Approval"


# ==============================================================================
# 20. W4.11 response contract remains fully compatible
# ==============================================================================
def test_w57_w411_response_contract_remains_compatible(generator):
    """Test 20: GroundedGenerator output satisfies the locked W4.11 StructuredAIResponse contract."""
    resp = generator.generate_structured_response("Bribery Act 2010 Section 1", top_k=2)

    assert isinstance(resp, StructuredAIResponse)
    assert resp.status in {ResponseStatus.GROUNDED, ResponseStatus.NEEDS_HUMAN_REVIEW}
    assert resp.grounded is True
    assert len(resp.citations) >= 1
    assert len(resp.provenance) >= 1
    assert len(resp.retrieved_evidence) >= 1
    assert resp.metadata.requires_human_review is True
    assert resp.to_external_status() in {"SUCCESS", "CONFLICT_DETECTED"}
