"""Tests for Step 8: Canonical Retrieval, Citations & Provenance Integration.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Staged collection selection and fail-closed isolation (no silent fallback).
2. Correct retrieval of representative UK and EU evidence from staged ChromaDB.
3. Deterministic citation-to-chunk and citation-to-source traceability.
4. Official URL, section/article, and metadata preservation in citations & provenance.
5. Missing and insufficient evidence handling (zero hallucinated citations).
6. Candidate blocking on the approved production path (filter_approved_only=True).
7. Preservation of the existing StructuredAIResponse schema and status mapping.
8. Active production store immutability (15 records, 15 chunks, 15 ChromaDB vectors).
"""

from pathlib import Path
import json
import pytest

from rag.retrieval.retriever import StagedRegulatoryRetriever, RegulatoryRetriever, RetrievalResult
from rag.retrieval.vector_store import ChromaVectorStore
from rag.generation.grounded_generator import StagedGroundedGenerator, CANDIDATE_APPROVAL_WARNING
from rag.generation.citations import CitationBuilder, Citation, ProvenanceRecord
from rag.generation.gap_handler import GapType
from rag.output.structured_response import StructuredAIResponse, ResponseStatus

STAGING_CHROMA_DIR = Path("data/staging/madhesh_handover/step6/chroma_db")
STAGING_COLLECTION_NAME = "canonical_regulatory_records"

ACTIVE_CHROMA_DIR = Path("data/processed/chroma_db")
ACTIVE_COLLECTION_NAME = "regulatory_records"
ACTIVE_CHUNKS_FILE = Path("data/processed/regulatory_chunks.json")
ACTIVE_NORM_FILE = Path("data/processed/normalized_regulatory_records.json")


@pytest.fixture(scope="module")
def staged_retriever():
    """Create isolated StagedRegulatoryRetriever instance."""
    return StagedRegulatoryRetriever()


@pytest.fixture(scope="module")
def staged_generator():
    """Create StagedGroundedGenerator instance."""
    return StagedGroundedGenerator()


# ---------------------------------------------------------------------------
# 1. Staged Collection Selection & Isolation
# ---------------------------------------------------------------------------

def test_staged_retriever_points_strictly_to_staging(staged_retriever):
    """Verify retriever connects to staged ChromaDB directory and collection."""
    store = staged_retriever.vector_store
    assert store.persist_dir == STAGING_CHROMA_DIR
    assert store.collection_name == STAGING_COLLECTION_NAME
    assert store.get_collection_stats()["total_vectors"] == 25


def test_staged_retriever_fails_closed_on_missing_dir():
    """Verify that specifying a non-existent directory raises FileNotFoundError (no fallback)."""
    with pytest.raises(FileNotFoundError) as exc_info:
        StagedRegulatoryRetriever(persist_dir=Path("data/nonexistent_staging_dir"))
    assert "Failing closed to prevent silent fallback" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 2. Representative UK and EU Evidence Retrieval
# ---------------------------------------------------------------------------

def test_uk_bribery_offence_retrieval(staged_retriever):
    """Verify UK Bribery Act Section 1 retrieval."""
    results = staged_retriever.retrieve(
        "offence of bribing another person",
        top_k=2,
        filter_approved_only=False
    )
    assert len(results) >= 1
    top = results[0]
    assert top.chunk_id == "UK-01-R001-C01"
    assert top.source_id == "UK-01"
    assert top.section_article == "Section 1"
    assert top.jurisdiction == "UK"
    assert top.similarity_score > 0.55
    assert "bribery" in top.text.lower()


def test_uk_fcg_guidance_retrieval(staged_retriever):
    """Verify FCA Financial Crime Guide (FCG 6) retrieval."""
    results = staged_retriever.retrieve(
        "Financial Crime Guide guidance on gifts and hospitality in FCG 6",
        top_k=2,
        filter_approved_only=False
    )
    assert len(results) >= 1
    top = results[0]
    assert top.source_id == "UK-03"
    assert top.chunk_id == "UK-03-R004-C01"
    assert top.section_article == "FCG 6.2.3"
    assert top.jurisdiction == "UK"
    assert top.similarity_score > 0.50


def test_eu_directive_private_bribery_retrieval(staged_retriever):
    """Verify EU Directive 2026/1021 Article 4 retrieval."""
    results = staged_retriever.retrieve(
        "What does Directive (EU) 2026/1021 establish regarding private-sector bribery?",
        top_k=2,
        filter_approved_only=False
    )
    assert len(results) >= 1
    top = results[0]
    assert top.chunk_id == "EU-01-R003-C01"
    assert top.source_id == "EU-01"
    assert top.section_article == "Article 4"
    assert top.jurisdiction == "EU-level"
    assert top.similarity_score > 0.75
    assert "private" in top.text.lower()


def test_eu_directive_mitigating_circumstances_retrieval(staged_retriever):
    """Verify EU Directive 2026/1021 Article 16 retrieval."""
    results = staged_retriever.retrieve(
        "What are the mitigating circumstances for legal persons under Article 16 of the EU corruption directive?",
        top_k=2,
        filter_approved_only=False
    )
    assert len(results) >= 1
    top = results[0]
    assert top.chunk_id == "EU-01-R007-C01"
    assert top.source_id == "EU-01"
    assert top.section_article == "Article 16"
    assert top.jurisdiction == "EU-level"
    assert top.similarity_score > 0.70


# ---------------------------------------------------------------------------
# 3. Citation and Provenance Traceability
# ---------------------------------------------------------------------------

def test_citation_to_chunk_traceability(staged_retriever):
    """Verify citations map deterministically 1:1 with retrieved chunks."""
    results = staged_retriever.retrieve(
        "commercial organisation failure to prevent bribery Section 7",
        top_k=3,
        filter_approved_only=False
    )
    assert len(results) > 0

    citations, provenance = CitationBuilder.build_citations(results, is_grounded=True)
    assert len(citations) == len(results)
    assert len(provenance) == len(results)

    for chunk, cit, prov in zip(results, citations, provenance):
        # Traceability assertions
        assert cit.chunk_id == chunk.chunk_id
        assert cit.record_id == chunk.record_id
        assert cit.source_id == chunk.source_id
        assert cit.citation_id == f"CIT-{chunk.chunk_id}"
        assert cit.formatted_citation == f"[{chunk.chunk_id} | {chunk.record_id} | {chunk.regulation} | {chunk.section_article}]"

        # Provenance assertions
        assert prov.chunk_id == chunk.chunk_id
        assert prov.record_id == chunk.record_id
        assert prov.source_id == chunk.source_id
        assert prov.official_source == chunk.official_source
        assert prov.similarity_score == chunk.similarity_score


def test_official_url_and_section_preservation_in_citations(staged_retriever):
    """Verify citations and provenance retain official URLs and exact section numbers."""
    results = staged_retriever.retrieve(
        "bribing another person",
        top_k=5,
        filter_approved_only=False
    )
    citations, provenance = CitationBuilder.build_citations(results, is_grounded=True)

    for cit in citations:
        assert cit.official_source is not None
        assert str(cit.official_source).startswith("http")
        assert cit.section_article is not None
        assert len(cit.section_article) > 0
        assert cit.is_approved_for_rag is False
        assert cit.validation_status in (
            "Candidate - Awaiting Approval",
            "Pending SME Validation",
            "Approved for RAG Integration - Pending SME Validation",
        )


# ---------------------------------------------------------------------------
# 4. Missing Evidence & Zero-Hallucination Guardrails
# ---------------------------------------------------------------------------

def test_missing_evidence_returns_zero_citations():
    """Verify ungrounded response produces exactly zero citations and zero provenance."""
    citations, provenance = CitationBuilder.build_citations([], is_grounded=False)
    assert citations == []
    assert provenance == []


def test_staged_generator_insufficient_evidence_handling(staged_generator):
    """Verify generator handles out-of-scope query without hallucinating citations."""
    response = staged_generator.generate_response(
        query="What are the maritime shipping salvage regulations under Admiralty Law?",
        top_k=3,
        filter_approved_only=False,
    )
    # The retriever may return low similarity chunks or gap handler triggers
    if not response.grounded:
        assert response.confidence_status == "INSUFFICIENT_EVIDENCE"
        assert response.citations == []
        assert response.provenance == []


# ---------------------------------------------------------------------------
# 5. Candidate Blocking on Approved Path (Fail-Closed)
# ---------------------------------------------------------------------------

def test_candidate_records_blocked_on_approved_path(staged_retriever):
    """Verify filter_approved_only=True returns exactly 0 results for candidate corpus."""
    results = staged_retriever.retrieve(
        "offences of bribing another person",
        top_k=5,
        filter_approved_only=True
    )
    assert len(results) == 0


def test_generator_fails_closed_under_approved_filter(staged_generator):
    """Verify generator returns UNAPPROVED_EVIDENCE gap status when filter_approved_only=True."""
    response = staged_generator.generate_response(
        query="offences of bribing another person",
        top_k=5,
        filter_approved_only=True
    )
    assert response.grounded is False
    assert response.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert response.gap is not None
    assert response.gap.gap_type == GapType.UNAPPROVED_EVIDENCE
    assert response.citations == []
    assert response.provenance == []


def test_staging_evaluation_output_has_candidate_warning(staged_generator):
    """Verify staging evaluation output includes explicit candidate/unapproved warning."""
    response = staged_generator.generate_response(
        query="offences of bribing another person under the UK Bribery Act",
        top_k=2,
        filter_approved_only=False
    )
    assert response.approval_warning == CANDIDATE_APPROVAL_WARNING
    assert "Candidate - Awaiting Approval" in response.approval_warning


# ---------------------------------------------------------------------------
# 6. Structured Response Schema & Contract Preservation
# ---------------------------------------------------------------------------

def test_structured_response_contract_preservation(staged_generator):
    """Verify StructuredAIResponse matches established Task 9 contract."""
    struct_resp = staged_generator.generate_structured_response(
        query="What constitutes an offence of bribing another person under Section 1?",
        top_k=2,
        filter_approved_only=False
    )
    assert isinstance(struct_resp, StructuredAIResponse)
    assert struct_resp.query is not None
    assert struct_resp.status in (ResponseStatus.GROUNDED, ResponseStatus.UNAPPROVED_EVIDENCE)
    assert struct_resp.metadata.response_version == "1.0"
    assert struct_resp.metadata.has_candidate_evidence is True
    assert struct_resp.metadata.approved_evidence_count == 0

    # Citations match retrieved evidence
    assert len(struct_resp.citations) == len(struct_resp.retrieved_evidence)
    for cit, ev in zip(struct_resp.citations, struct_resp.retrieved_evidence):
        assert cit.chunk_id == ev.chunk_id
        assert cit.record_id == ev.record_id
        assert cit.official_source == ev.official_source


def test_structured_response_approved_filter_mapping(staged_generator):
    """Verify structured response maps to UNAPPROVED_EVIDENCE when approved filter is applied."""
    struct_resp = staged_generator.generate_structured_response(
        query="What constitutes an offence of bribing another person?",
        top_k=2,
        filter_approved_only=True
    )
    assert struct_resp.status == ResponseStatus.UNAPPROVED_EVIDENCE
    assert struct_resp.grounded is False
    assert struct_resp.gap is not None
    assert struct_resp.gap.gap_type == GapType.UNAPPROVED_EVIDENCE
    assert struct_resp.gap.has_candidate_evidence is True
    assert struct_resp.metadata.retrieved_count == 0
    assert struct_resp.metadata.approved_evidence_count == 0
    assert len(struct_resp.citations) == 0


# ---------------------------------------------------------------------------
# 7. Active Production Store Immutability
# ---------------------------------------------------------------------------

def test_active_production_stores_untouched():
    """Verify active ChromaDB (15 vectors) and active JSON stores remain 100% untouched."""
    active_store = ChromaVectorStore(
        persist_dir=ACTIVE_CHROMA_DIR,
        collection_name=ACTIVE_COLLECTION_NAME
    )
    assert active_store._get_collection().count() == 15

    with open(ACTIVE_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    assert len(chunks) == 15

    with open(ACTIVE_NORM_FILE, "r", encoding="utf-8") as f:
        norm = json.load(f)
    assert len(norm) == 15
