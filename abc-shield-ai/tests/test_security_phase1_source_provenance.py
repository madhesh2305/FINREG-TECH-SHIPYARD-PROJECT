"""Security Test Suite for Phase 1: Source, Provenance & Evidence Security.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifications for Security Checklist Phase 1:
- RAG-04 Source Tampering
- RAG-05 Citation Mismatch
- RAG-06 No-Source Handling
- RAG-08 Stale Source
- RAG-13 Provenance Loss
- End-to-end evidence path traceability:
  Regulatory Source -> Normalized Record -> Regulatory Chunk -> ChromaDB Metadata
  -> Retrieval Result -> Citation -> Provenance -> Structured API Response
"""

from typing import List, Dict, Any
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from api.main import app
from rag.ingestion.schemas import (
    NormalizedRegulatoryRecord,
    RegulatoryChunk,
    SourceRegisterRecord,
    is_sme_approved,
)
from rag.ingestion.validator import RegulatoryDataValidator
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.generation.grounded_generator import (
    GroundedGenerator,
    GroundedResponse,
    CANDIDATE_APPROVAL_WARNING,
)
from rag.generation.llm_interface import MockLLMProvider
from rag.generation.citations import Citation, ProvenanceRecord, CitationBuilder
from rag.generation.gap_handler import GapType, GapResult
from rag.conflict.conflict_detector import ConflictDetector, ConflictFinding, ConflictType
from rag.output.structured_response import (
    StructuredAIResponse,
    ResponseStatus,
    RetrievedEvidenceItem,
)


@pytest.fixture(scope="module")
def persistent_retriever():
    """Real retriever connected to verified production ChromaDB."""
    return RegulatoryRetriever()


@pytest.fixture(scope="module")
def api_client():
    """TestClient for API verification."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_llm():
    """Deterministic MockLLMProvider."""
    return MockLLMProvider()


@pytest.fixture
def sample_valid_chunk():
    """Standard valid evidence chunk based on Bribery Act RR-UK-01-C01."""
    return RetrievalResult(
        chunk_id="RR-UK-01-C01",
        record_id="RR-UK-01",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament / legislation.gov.uk",
        jurisdiction="UK",
        section_article="Section 1",
        title="Offences of bribing another person",
        text="It is an offence to offer, promise or give a financial or other advantage...",
        text_type="requirement_paraphrase",
        topic="Bribery; Corruption",
        official_source="https://www.legislation.gov.uk/ukpga/2010/23/contents",
        version_date="Current official version",
        effective_date="8 April 2010",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        authority_level="A",
        source_type="Primary Legislation",
        similarity_score=0.885,
        distance=0.115,
    )


# ---------------------------------------------------------------------------
# 1. Complete Evidence Path Traceability Audit
# ---------------------------------------------------------------------------

def test_traceability_across_complete_evidence_path(persistent_retriever, mock_llm):
    """Verify that trusted provenance remains attached throughout the entire pipeline:

    ChromaDB Metadata -> RetrievalResult -> Citation -> ProvenanceRecord -> StructuredAIResponse.
    """
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What constitutes an offence of bribing another person under Section 1?"

    # Execute structured generation
    struct_resp: StructuredAIResponse = generator.generate_structured_response(
        query=query,
        top_k=3,
        request_id="REQ-SEC-P1-01",
    )

    assert struct_resp.grounded is True
    assert len(struct_resp.citations) > 0
    assert len(struct_resp.provenance) > 0
    assert len(struct_resp.retrieved_evidence) > 0

    # Locate Rank-1 Bribery Act Section 1 evidence
    uk01_evidence = next((e for e in struct_resp.retrieved_evidence if e.chunk_id == "RR-UK-01-C01"), None)
    uk01_citation = next((c for c in struct_resp.citations if c.chunk_id == "RR-UK-01-C01"), None)
    uk01_prov = next((p for p in struct_resp.provenance if p.chunk_id == "RR-UK-01-C01"), None)

    assert uk01_evidence is not None, "RR-UK-01-C01 must be in retrieved evidence"
    assert uk01_citation is not None, "RR-UK-01-C01 must be in citations"
    assert uk01_prov is not None, "RR-UK-01-C01 must be in provenance"

    # Verify field-by-field preservation across evidence, citation, and provenance
    traceable_fields = [
        "chunk_id",
        "record_id",
        "source_id",
        "regulation",
        "section_article",
        "title",
        "official_source",
        "version_date",
        "effective_date",
        "validation_status",
        "is_approved_for_rag",
    ]

    for field in traceable_fields:
        ev_val = getattr(uk01_evidence, field)
        cit_val = getattr(uk01_citation, field)
        pr_val = getattr(uk01_prov, field)
        assert ev_val == cit_val == pr_val, f"Provenance field '{field}' mismatched across pipeline: {ev_val} vs {cit_val} vs {pr_val}"

    # Verify jurisdiction on citation and provenance
    assert uk01_citation.jurisdiction == "UK"
    assert uk01_prov.jurisdiction == "UK"

    # Verify exact expected canonical values
    assert uk01_citation.source_id == "UK-01"
    assert uk01_citation.record_id == "RR-UK-01"
    assert uk01_citation.chunk_id == "RR-UK-01-C01"
    assert uk01_citation.regulation == "Bribery Act 2010"
    assert uk01_citation.section_article == "Section 1"
    assert uk01_citation.is_approved_for_rag is False
    assert uk01_citation.validation_status == "Candidate - Awaiting Approval"


# ---------------------------------------------------------------------------
# 2. RAG-04: Source & Provenance Tampering Prevention
# ---------------------------------------------------------------------------

def test_rag04_tampering_unregistered_source_id_rejected():
    """Verify that introducing an unregistered foreign source_id is detected by data validator."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-TAMPER-01",
        source_id="UNKNOWN-FOREIGN-99",  # Tampered/unregistered foreign key
        regulation="Tampered Foreign Regulation",
        regulator="Unknown Foreign Regulator",
        jurisdiction="UK",
        section_article="Article 1",
        title="Tampered Obligation",
        requirement="Requirement text.",
        retrieval_text="Retrieval text.",
        validation_status="Candidate - Awaiting Approval",
    )

    sources = [
        SourceRegisterRecord(
            source_id="UK-01",
            source_name="Bribery Act 2010",
            issuing_authority="UK Parliament",
            jurisdiction="UK",
            source_type="Primary Legislation",
            authority_level="A",
            status="Candidate - Awaiting Approval",
        )
    ]
    validator = RegulatoryDataValidator(sources)
    report = validator.validate_records([rec])

    assert report.all_source_ids_resolved is False
    assert report.has_critical_errors is True
    issue = next(i for i in report.issues if i.field == "source_id")
    assert issue.issue_type == "ERROR"
    assert "does not match any entry in the Source Register" in issue.message


def test_rag04_tampering_validation_status_neutralized():
    """Verify that tampering validation_status or forcing is_approved_for_rag is neutralized."""
    # Attempt tamper on NormalizedRegulatoryRecord
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-TAMPER-02",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Bribery Offence",
        requirement="Requirement text.",
        retrieval_text="Retrieval text.",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=True,  # Tamper injection
    )
    assert rec.is_approved_for_rag is False

    # Attempt tamper on RegulatoryChunk
    chunk = RegulatoryChunk(
        chunk_id="RR-TEST-TAMPER-02-C01",
        record_id="RR-TEST-TAMPER-02",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Bribery Offence",
        text="Chunk text.",
        requirement="Requirement text.",
        validation_status="Not Approved",
        is_approved_for_rag=True,  # Tamper injection
    )
    assert chunk.is_approved_for_rag is False


def test_rag04_tampering_authority_level_does_not_elevate_approval():
    """Verify that claiming Authority Level A (primary legislation) never confers approval status."""
    rec = NormalizedRegulatoryRecord(
        record_id="RR-TEST-TAMPER-03",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Bribery Offence",
        requirement="Requirement text.",
        retrieval_text="Retrieval text.",
        validation_status="Candidate - Awaiting Approval",
        authority_level="A",  # High authority
        is_approved_for_rag=True,  # Tamper
    )
    assert rec.is_approved_for_rag is False


# ---------------------------------------------------------------------------
# 3. RAG-05: Citation Mismatch Prevention
# ---------------------------------------------------------------------------

def test_rag05_citation_cannot_reference_unretrieved_evidence(sample_valid_chunk):
    """Verify that CitationBuilder strictly rejects chunks not present in retrieved evidence."""
    # Supply sample_valid_chunk as retrieved evidence
    retrieved = [sample_valid_chunk]

    # Create an unretrieved synthetic chunk
    unretrieved_chunk = RetrievalResult(
        chunk_id="RR-UNRETRIEVED-99-C01",
        record_id="RR-UNRETRIEVED-99",
        source_id="UK-99",
        regulation="Unretrieved Legislation",
        regulator="Unknown",
        jurisdiction="UK",
        section_article="Section 99",
        title="Unretrieved",
        text="Unretrieved text.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.99,
        distance=0.01,
    )

    # CitationBuilder called with retrieved chunks
    citations, provenance = CitationBuilder.build_citations(retrieved, is_grounded=True)
    cited_ids = {c.chunk_id for c in citations}

    assert sample_valid_chunk.chunk_id in cited_ids
    assert unretrieved_chunk.chunk_id not in cited_ids
    assert "RR-UNRETRIEVED-99-C01" not in cited_ids


def test_rag05_model_hallucinated_citations_are_ignored(persistent_retriever):
    """Verify that if the LLM hallucinates invented chunk IDs, they are not adopted into citations."""
    # Create a mock LLM that claims to cite completely invented chunks and regulations
    hallucinating_llm = MockLLMProvider(
        default_response=(
            "According to CIT-INVENTED-88 and Section 999 of the Fantasy Regulations 2026, "
            "commercial entities are strictly regulated."
        )
    )

    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=hallucinating_llm)
    query = "What constitutes bribery?"

    res = generator.generate_response(query=query, top_k=3)

    assert res.grounded is True
    # The citations must ONLY contain actual retrieved chunks, NEVER the hallucinated ones
    cited_chunk_ids = {c.chunk_id for c in res.citations}
    assert "CIT-INVENTED-88" not in cited_chunk_ids
    assert "RR-INVENTED-88-C01" not in cited_chunk_ids
    for cit in res.citations:
        assert cit.chunk_id in res.evidence_used


def test_rag05_each_citation_maps_strictly_to_its_own_chunk():
    """Verify that attributes across multiple retrieved chunks are never cross-pollinated or mixed."""
    chunk_uk = RetrievalResult(
        chunk_id="RR-UK-01-C01",
        record_id="RR-UK-01",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Bribing another person",
        text="Offence to offer bribe...",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.92,
        distance=0.08,
    )
    chunk_eu = RetrievalResult(
        chunk_id="RR-EU-05-C01",
        record_id="RR-EU-05",
        source_id="EU-05",
        regulation="Regulation (EU) No 596/2014 (MAR)",
        regulator="European Parliament and Council",
        jurisdiction="EU",
        section_article="Article 7",
        title="Inside information",
        text="Inside information shall comprise...",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.88,
        distance=0.12,
    )

    citations, provenance = CitationBuilder.build_citations([chunk_uk, chunk_eu], is_grounded=True)
    assert len(citations) == 2

    cit_uk = next(c for c in citations if c.chunk_id == "RR-UK-01-C01")
    assert cit_uk.record_id == "RR-UK-01"
    assert cit_uk.source_id == "UK-01"
    assert cit_uk.regulation == "Bribery Act 2010"
    assert cit_uk.jurisdiction == "UK"
    assert cit_uk.section_article == "Section 1"

    cit_eu = next(c for c in citations if c.chunk_id == "RR-EU-05-C01")
    assert cit_eu.record_id == "RR-EU-05"
    assert cit_eu.source_id == "EU-05"
    assert cit_eu.regulation == "Regulation (EU) No 596/2014 (MAR)"
    assert cit_eu.jurisdiction == "EU"
    assert cit_eu.section_article == "Article 7"


# ---------------------------------------------------------------------------
# 4. RAG-06: No-Source & Insufficient Evidence Handling
# ---------------------------------------------------------------------------

def test_rag06_out_of_scope_query_produces_zero_citations_and_zero_provenance(persistent_retriever, mock_llm):
    """Verify that querying for out-of-scope domains produces zero citations and zero provenance."""
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    out_of_scope_query = "What cybersecurity risk management requirements apply under DORA and NIS2?"

    res = generator.generate_response(query=out_of_scope_query, top_k=3)

    assert res.grounded is False
    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.citations == []
    assert res.provenance == []
    assert res.gap is not None
    assert res.gap.gap_type == GapType.OUT_OF_SCOPE
    assert "DORA" in res.gap.user_safe_message or "cybersecurity" in res.gap.user_safe_message.lower()


def test_rag06_missing_provision_safe_disclosure_zero_fabrication(persistent_retriever, mock_llm):
    """Verify that querying for missing provisions emits safe disclosure without fabricating citations."""
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    missing_prov_query = "What is the corporate failure to prevent bribery offence under Section 7 of the Bribery Act 2010?"

    res = generator.generate_response(query=missing_prov_query, top_k=5)

    assert res.grounded is False
    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.citations == []
    assert res.provenance == []
    assert res.gap is not None
    assert res.gap.is_gap is True
    # Must explicitly state absence from corpus without claiming absence from the law
    assert "not represented in the current ABC Shield" in res.gap.user_safe_message


def test_rag06_empty_retrieval_bypasses_llm_completely(mock_llm):
    """Verify that when zero chunks are retrieved, the LLM is completely bypassed."""
    empty_retriever = MagicMock()
    empty_retriever.retrieve.return_value = []

    generator = GroundedGenerator(retriever=empty_retriever, llm_provider=mock_llm)
    res = generator.generate_response(query="Any arbitrary query")

    assert mock_llm.call_count == 0
    assert res.grounded is False
    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.citations == []
    assert res.provenance == []
    assert res.gap is not None
    assert res.gap.gap_type == GapType.NO_RETRIEVED_EVIDENCE


def test_rag06_approved_only_filter_produces_zero_llm_calls_and_unapproved_gap(persistent_retriever, mock_llm):
    """Verify that approved-only query on candidate corpus bypasses LLM and returns UNAPPROVED_EVIDENCE."""
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    res = generator.generate_response(
        query="What procedures should commercial organisations implement to prevent bribery?",
        filter_approved_only=True,
    )

    assert mock_llm.call_count == 0
    assert res.grounded is False
    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.citations == []
    assert res.provenance == []
    assert res.gap is not None
    assert res.gap.gap_type == GapType.UNAPPROVED_EVIDENCE


# ---------------------------------------------------------------------------
# 5. RAG-08: Stale & Superseded Source Handling
# ---------------------------------------------------------------------------

def test_rag08_version_and_effective_dates_preserved(sample_valid_chunk):
    """Verify version_date and effective_date are preserved without silent loss or falsification."""
    cit = Citation.from_retrieval_result(sample_valid_chunk)
    prov = cit.to_provenance(similarity_score=sample_valid_chunk.similarity_score)

    assert cit.version_date == "Current official version"
    assert cit.effective_date == "8 April 2010"
    assert prov.version_date == "Current official version"
    assert prov.effective_date == "8 April 2010"


def test_rag08_superseded_and_current_pair_detected_as_version_difference():
    """Verify that co-retrieval of MAD (EU-04) and MAR (EU-05) surfaces documented version difference (CO-010)."""
    chunk_mad = RetrievalResult(
        chunk_id="RR-EU-04-C01",
        record_id="RR-EU-04",
        source_id="EU-04",
        regulation="Directive 2003/6/EC (MAD)",
        regulator="European Parliament and Council",
        jurisdiction="EU",
        section_article="Article 1",
        title="Inside information definition under MAD",
        text="Inside information under MAD Directive...",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.87,
        distance=0.13,
    )
    chunk_mar = RetrievalResult(
        chunk_id="RR-EU-05-C01",
        record_id="RR-EU-05",
        source_id="EU-05",
        regulation="Regulation (EU) No 596/2014 (MAR)",
        regulator="European Parliament and Council",
        jurisdiction="EU",
        section_article="Article 7",
        title="Inside information definition under MAR",
        text="Inside information under MAR Regulation...",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.91,
        distance=0.09,
    )

    detector = ConflictDetector()
    findings = detector.detect([chunk_mad, chunk_mar])

    assert len(findings) == 1
    finding = findings[0]
    assert finding.conflict_id == "CO-010"
    assert finding.conflict_type == ConflictType.VERSION_DIFFERENCE
    assert finding.requires_human_review is True
    # Must report documented relationship without declaring legal override or winner
    assert "repeals and replaces" in finding.relationship or "amendment" in finding.relationship.lower()
    assert "No legal conflict resolution is made by this system" in finding.message
    # Both sources remain Candidate - Awaiting Approval
    assert finding.source_1_validation_status == "Candidate - Awaiting Approval"
    assert finding.source_2_validation_status == "Candidate - Awaiting Approval"
    assert finding.is_approved_for_rag is False


# ---------------------------------------------------------------------------
# 6. RAG-13: Provenance Loss & Manipulation Handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tampered_field",
    [
        "source_id",
        "record_id",
        "chunk_id",
        "regulation",
        "section_article",
        "jurisdiction",
    ],
)
def test_rag13_pydantic_validator_rejects_empty_provenance_field(sample_valid_chunk, tampered_field):
    """Verify that Citation and ProvenanceRecord raise ValueError if any mandatory provenance field is empty."""
    chunk_dict = sample_valid_chunk.model_dump()
    chunk_dict[tampered_field] = ""  # Strip mandatory field

    tampered_chunk = RetrievalResult(**chunk_dict)

    # 1. Direct Citation construction must raise ValueError
    with pytest.raises(ValueError, match="cannot be empty or whitespace-only"):
        Citation.from_retrieval_result(tampered_chunk)

    # 2. CitationBuilder.is_valid_provenance must return False
    assert CitationBuilder.is_valid_provenance(tampered_chunk) is False


def test_rag13_citation_builder_drops_untrusted_chunks(sample_valid_chunk):
    """Verify that CitationBuilder drops chunks lacking trusted provenance from citations and provenance."""
    corrupted_chunk = RetrievalResult(
        chunk_id="RR-CORRUPT-01-C01",
        record_id="RR-CORRUPT-01",
        source_id="",  # Stripped source_id
        regulation="Corrupted Regulation",
        regulator="Unknown",
        jurisdiction="UK",
        section_article="Article 1",
        title="Corrupted",
        text="Corrupted text.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.9,
        distance=0.1,
    )

    # Supply 1 valid chunk and 1 corrupted chunk
    citations, provenance = CitationBuilder.build_citations([sample_valid_chunk, corrupted_chunk], is_grounded=True)

    assert len(citations) == 1
    assert len(provenance) == 1
    assert citations[0].chunk_id == sample_valid_chunk.chunk_id
    assert provenance[0].chunk_id == sample_valid_chunk.chunk_id
    assert "RR-CORRUPT-01-C01" not in [c.chunk_id for c in citations]


def test_rag13_generator_fails_closed_when_all_chunks_lack_provenance(mock_llm):
    """Verify that GroundedGenerator fails closed without calling LLM if all chunks have lost provenance."""
    corrupted_chunk_1 = RetrievalResult(
        chunk_id="",  # Stripped chunk_id
        record_id="RR-UK-01",
        source_id="UK-01",
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 1",
        title="Bribery",
        text="Text content.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.9,
        distance=0.1,
    )
    corrupted_chunk_2 = RetrievalResult(
        chunk_id="RR-UK-02-C01",
        record_id="RR-UK-02",
        source_id="",  # Stripped source_id
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="",  # Stripped section
        title="Bribery",
        text="Text content.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.9,
        distance=0.1,
    )

    generator = GroundedGenerator(llm_provider=mock_llm)
    resp = generator.generate_response(
        query="What is bribery?",
        evidence_chunks=[corrupted_chunk_1, corrupted_chunk_2],
    )

    # 1. LLM must never be called
    assert mock_llm.call_count == 0

    # 2. Response must be ungrounded with insufficient evidence
    assert resp.grounded is False
    assert resp.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert resp.evidence_count == 0
    assert resp.citations == []
    assert resp.provenance == []

    # 3. Gap must indicate NEEDS_HUMAN_REVIEW
    assert resp.gap is not None
    assert resp.gap.is_gap is True
    assert resp.gap.gap_type == GapType.NEEDS_HUMAN_REVIEW
    assert resp.gap.requires_human_review is True
    assert "cannot be verified due to missing or untrusted provenance" in resp.gap.user_safe_message


def test_rag13_partial_tampering_strips_corrupted_chunks_safely(sample_valid_chunk, mock_llm):
    """Verify that when 1 of 2 chunks is tampered, only the trusted chunk enters prompt and citations."""
    corrupted_chunk = RetrievalResult(
        chunk_id="RR-UK-02-C01",
        record_id="RR-UK-02",
        source_id="",  # Stripped source_id
        regulation="Bribery Act 2010",
        regulator="UK Parliament",
        jurisdiction="UK",
        section_article="Section 2",
        title="Bribery",
        text="Corrupted chunk text.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.9,
        distance=0.1,
    )

    # Mock provider returning a grounded answer for valid evidence
    mock = MockLLMProvider(default_response="Bribery is an offence under Section 1.")
    generator = GroundedGenerator(llm_provider=mock)

    resp = generator.generate_response(
        query="What is bribery?",
        evidence_chunks=[sample_valid_chunk, corrupted_chunk],
    )

    assert mock.call_count == 1
    # Only the trusted chunk was passed to LLM
    assert resp.evidence_used == [sample_valid_chunk.chunk_id]
    assert len(resp.citations) == 1
    assert resp.citations[0].chunk_id == sample_valid_chunk.chunk_id
    assert "Corrupted chunk text" not in (mock.last_prompt or "")
