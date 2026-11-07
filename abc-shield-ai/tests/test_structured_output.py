"""Tests for Task 9: Structured AI Output Contract.

Validates that StructuredAIResponse provides a stable, machine-readable JSON schema
unifying Tasks 4–8 with deterministic status mapping, full metadata traceability,
and strict safety guardrails (no LLM-invented citations, GAPs, or conflicts).
"""

import json
import pytest
from typing import List, Optional

from rag.output import (
    ResponseStatus,
    RetrievedEvidenceItem,
    ResponseMetadata,
    StructuredAIResponse,
    StructuredResponseBuilder,
)
from rag.generation.grounded_generator import GroundedGenerator, GroundedResponse
from rag.generation.citations import Citation, ProvenanceRecord, CitationBuilder
from rag.generation.gap_handler import GapType, GapResult, GapHandler
from rag.generation.llm_interface import MockLLMProvider
from rag.conflict.conflict_detector import ConflictDetector, ConflictFinding, ConflictType
from rag.retrieval.retriever import RetrievalResult


def _make_chunk(
    chunk_id: str,
    record_id: str,
    source_id: str,
    regulation: str,
    section: str = "Section 1",
    validation_status: str = "Candidate - Awaiting Approval",
    is_approved_for_rag: bool = False,
    similarity_score: float = 0.88,
) -> RetrievalResult:
    """Helper to construct synthetic RetrievalResult fixtures."""
    return RetrievalResult(
        chunk_id=chunk_id,
        record_id=record_id,
        source_id=source_id,
        regulation=regulation,
        regulator="Authority",
        jurisdiction="UK" if source_id.startswith("UK") else "EU",
        section_article=section,
        title=f"Title for {section}",
        text=f"Sample regulatory requirement text for {chunk_id}",
        text_type="requirement_paraphrase",
        topic="Anti-Bribery",
        official_source="https://example.com/source",
        version_date="2024-01-01",
        effective_date="2024-01-01",
        validation_status=validation_status,
        is_approved_for_rag=is_approved_for_rag,
        similarity_score=similarity_score,
        distance=round(1.0 - similarity_score, 4),
    )


# ---------------------------------------------------------------------------
# Test 1 & 2: Grounded Response status and answer
# ---------------------------------------------------------------------------

def test_1_grounded_response_produces_status_grounded():
    """Grounded generation with evidence produces status == GROUNDED."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    grounded_resp = GroundedResponse(
        query="What offences exist under Bribery Act?",
        answer="The Bribery Act 2010 defines offences.",
        evidence_used=["RR-UK-01-C01"],
        confidence_status="GROUNDED",
        grounded=True,
        gap=None,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, retrieved_chunks=[chunk])
    assert structured.status == ResponseStatus.GROUNDED
    assert structured.grounded is True


def test_2_grounded_response_contains_answer():
    """Grounded response preserves the generated answer string verbatim."""
    grounded_resp = GroundedResponse(
        query="What offences exist under Bribery Act?",
        answer="Direct answer text based on retrieved evidence.",
        evidence_used=["RR-UK-01-C01"],
        confidence_status="GROUNDED",
        grounded=True,
    )
    structured = StructuredResponseBuilder.build(grounded_resp)
    assert structured.answer == "Direct answer text based on retrieved evidence."


# ---------------------------------------------------------------------------
# Test 3 & 4: Preservation of Citations and Provenance
# ---------------------------------------------------------------------------

def test_3_grounded_response_preserves_citations():
    """Citations from Task 6 are preserved intact in StructuredAIResponse."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    citations, provenance = CitationBuilder.build_citations([chunk], is_grounded=True)
    grounded_resp = GroundedResponse(
        query="Bribery query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        citations=citations,
        provenance=provenance,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert len(structured.citations) == 1
    assert structured.citations[0].citation_id == "CIT-RR-UK-01-C01"
    assert structured.citations[0].chunk_id == "RR-UK-01-C01"


def test_4_grounded_response_preserves_provenance():
    """Provenance records from Task 6 are preserved intact."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    citations, provenance = CitationBuilder.build_citations([chunk], is_grounded=True)
    grounded_resp = GroundedResponse(
        query="Bribery query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        citations=citations,
        provenance=provenance,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert len(structured.provenance) == 1
    assert structured.provenance[0].chunk_id == "RR-UK-01-C01"
    assert structured.provenance[0].source_id == "UK-01"


# ---------------------------------------------------------------------------
# Test 5 & 6: Conflicts and Retrieved Evidence
# ---------------------------------------------------------------------------

def test_5_grounded_response_preserves_conflicts():
    """Conflict findings from Task 8 are preserved without alteration."""
    chunk1 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk2 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    detector = ConflictDetector()
    conflicts = detector.detect([chunk1, chunk2])

    grounded_resp = GroundedResponse(
        query="Procedures query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        conflicts=conflicts,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk1, chunk2])
    assert len(structured.conflicts) == 1
    assert structured.conflicts[0].conflict_id == "CO-001"
    assert structured.conflicts[0].both_sources_retrieved is True


def test_6_grounded_response_includes_retrieved_evidence():
    """Retrieved evidence chunks are formatted as RetrievedEvidenceItem items."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010", similarity_score=0.89)
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert len(structured.retrieved_evidence) == 1
    evidence = structured.retrieved_evidence[0]
    assert evidence.chunk_id == "RR-UK-01-C01"
    assert evidence.source_id == "UK-01"
    assert evidence.similarity_score == 0.89
    assert evidence.similarity == 0.89
    assert evidence.text == chunk.text


# ---------------------------------------------------------------------------
# Test 7, 8, 9, 10: Status and GAP Mapping
# ---------------------------------------------------------------------------

def test_7_empty_retrieval_produces_correct_gap_and_status():
    """Empty retrieval maps to status == INSUFFICIENT_EVIDENCE with NO_RETRIEVED_EVIDENCE gap."""
    gap = GapHandler.analyze_gap("Empty query test", [], is_grounded=False)
    grounded_resp = GroundedResponse(
        query="Empty query test",
        answer="No matching regulatory records were found.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [])
    assert structured.status == ResponseStatus.INSUFFICIENT_EVIDENCE
    assert structured.grounded is False
    assert structured.gap is not None
    assert structured.gap.gap_type == GapType.NO_RETRIEVED_EVIDENCE
    assert structured.citations == []
    assert structured.retrieved_evidence == []


def test_8_out_of_scope_gap_maps_to_out_of_scope_status():
    """Out-of-scope GAP (e.g. cybersecurity/DORA) maps to status == OUT_OF_SCOPE."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    gap = GapHandler.analyze_gap("What are DORA cybersecurity rules?", [chunk], is_grounded=False)
    grounded_resp = GroundedResponse(
        query="What are DORA cybersecurity rules?",
        answer="Out of scope answer.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert structured.status == ResponseStatus.OUT_OF_SCOPE
    assert structured.gap.gap_type == GapType.OUT_OF_SCOPE
    assert structured.grounded is False


def test_9_unapproved_evidence_gap_maps_to_unapproved_evidence_status():
    """Unapproved evidence GAP maps to status == UNAPPROVED_EVIDENCE."""
    gap = GapHandler.analyze_gap("Query", [], is_grounded=False, filter_approved_only=True)
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Unapproved answer.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [])
    assert structured.status == ResponseStatus.UNAPPROVED_EVIDENCE
    assert structured.gap.gap_type == GapType.UNAPPROVED_EVIDENCE
    assert structured.grounded is False


def test_10_insufficient_evidence_gap_maps_to_insufficient_evidence_status():
    """Missing specific provision gap maps to status == INSUFFICIENT_EVIDENCE."""
    chunk = _make_chunk("RR-UK-07-C01", "RR-UK-07", "UK-07", "Practice Note", section="Principle 3")
    gap = GapHandler.analyze_gap("What does Section 1 say?", [chunk], is_grounded=False)
    grounded_resp = GroundedResponse(
        query="What does Section 1 say?",
        answer="Insufficient evidence.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert structured.status == ResponseStatus.INSUFFICIENT_EVIDENCE
    assert structured.gap.gap_type == GapType.MISSING_SPECIFIC_PROVISION
    assert structured.grounded is False


# ---------------------------------------------------------------------------
# Test 11, 12, 13: Integrity & Provenance Whitelisting
# ---------------------------------------------------------------------------

def test_11_citation_chunk_ids_remain_whitelisted():
    """All citation chunk IDs strictly belong to the retrieved chunk IDs."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    citations, provenance = CitationBuilder.build_citations([chunk], is_grounded=True)
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        citations=citations,
        provenance=provenance,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    retrieved_ids = {e.chunk_id for e in structured.retrieved_evidence}
    for cit in structured.citations:
        assert cit.chunk_id in retrieved_ids


def test_12_conflict_ids_preserved_from_task_8():
    """Conflict IDs are preserved exactly as determined in Task 8."""
    chunk1 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk2 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    conflicts = ConflictDetector().detect([chunk1, chunk2])
    grounded_resp = GroundedResponse(
        query="Query", answer="Answer", confidence_status="GROUNDED", grounded=True, conflicts=conflicts
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk1, chunk2])
    assert structured.conflicts[0].conflict_id == "CO-001"


def test_13_source_ids_preserved():
    """Source IDs in retrieved evidence match the original source register values."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    grounded_resp = GroundedResponse(
        query="Query", answer="Answer", confidence_status="GROUNDED", grounded=True
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert structured.retrieved_evidence[0].source_id == "UK-01"


# ---------------------------------------------------------------------------
# Test 14, 15, 16: Guardrails Against LLM Fabrication
# ---------------------------------------------------------------------------

def test_14_gap_information_not_generated_by_llm():
    """GAP information originates exclusively from Task 7, never from LLM."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    gap = GapHandler.analyze_gap("DORA cybersecurity", [chunk], is_grounded=False)
    grounded_resp = GroundedResponse(
        query="DORA cybersecurity",
        answer="LLM says something completely random.",
        confidence_status="INSUFFICIENT_EVIDENCE",
        grounded=False,
        gap=gap,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert structured.gap.gap_type == GapType.OUT_OF_SCOPE
    assert "cybersecurity" in structured.gap.user_safe_message.lower()
    assert structured.gap.user_safe_message != grounded_resp.answer


def test_15_conflict_information_not_generated_by_llm():
    """Conflict findings originate strictly from the controlled register in Task 8."""
    grounded_resp = GroundedResponse(
        query="Query",
        answer="I think UK-01 overrides EU-01.",  # LLM hallucinates a conflict
        confidence_status="GROUNDED",
        grounded=True,
        conflicts=[],  # Task 8 found no conflict
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [])
    assert structured.conflicts == []


def test_16_provenance_not_generated_by_llm():
    """Provenance chains are constructed deterministically without LLM intervention."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    _, provenance = CitationBuilder.build_citations([chunk], is_grounded=True)
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        provenance=provenance,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk])
    assert len(structured.provenance) == 1
    assert structured.provenance[0].record_id == "RR-UK-01"


# ---------------------------------------------------------------------------
# Test 17, 18, 19, 20: Schema, Serialization & Defaults
# ---------------------------------------------------------------------------

def test_17_output_is_json_serializable():
    """StructuredAIResponse serializes cleanly to valid JSON."""
    chunk = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    citations, provenance = CitationBuilder.build_citations([chunk], is_grounded=True)
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        citations=citations,
        provenance=provenance,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk], request_id="REQ-12345")
    json_str = structured.model_dump_json(indent=2)
    parsed = json.loads(json_str)

    assert parsed["request_id"] == "REQ-12345"
    assert parsed["status"] == "GROUNDED"
    assert parsed["grounded"] is True
    assert isinstance(parsed["citations"], list)
    assert isinstance(parsed["provenance"], list)
    assert isinstance(parsed["retrieved_evidence"], list)
    assert isinstance(parsed["metadata"], dict)


def test_18_lists_default_to_empty_lists_rather_than_null():
    """Lists default to empty lists rather than null in StructuredAIResponse."""
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
    )
    structured = StructuredResponseBuilder.build(grounded_resp)
    assert structured.citations == []
    assert structured.provenance == []
    assert structured.conflicts == []
    assert structured.retrieved_evidence == []


def test_19_optional_gap_is_null_when_no_gap():
    """When a response is grounded, gap is null (None)."""
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        gap=None,
    )
    structured = StructuredResponseBuilder.build(grounded_resp)
    assert structured.gap is None


def test_20_optional_request_id_works_when_omitted():
    """Request ID is optional and defaults to None when omitted."""
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
    )
    structured = StructuredResponseBuilder.build(grounded_resp)
    assert structured.request_id is None


# ---------------------------------------------------------------------------
# Test 21, 22, 23, 24: Metadata & Non-Disclosure of Internal Reasoning
# ---------------------------------------------------------------------------

def test_21_metadata_counts_are_deterministic():
    """Metadata counts accurately reflect counts of underlying elements."""
    chunk1 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010", is_approved_for_rag=True)
    chunk2 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act Guidance", is_approved_for_rag=False)
    citations, provenance = CitationBuilder.build_citations([chunk1, chunk2], is_grounded=True)
    conflicts = ConflictDetector().detect([chunk1, chunk2])

    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
        citations=citations,
        provenance=provenance,
        conflicts=conflicts,
        gap=None,
    )
    structured = StructuredResponseBuilder.build(grounded_resp, [chunk1, chunk2])

    assert structured.metadata.retrieved_count == 2
    assert structured.metadata.approved_evidence_count == 1
    assert structured.metadata.citation_count == 2
    assert structured.metadata.conflict_count == 1
    assert structured.metadata.has_gap is False
    assert structured.metadata.response_version == "1.0"


def test_22_no_hidden_internal_prompts_exposed():
    """Structured response schema does not contain raw system grounding prompts."""
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
    )
    structured = StructuredResponseBuilder.build(grounded_resp)
    dumped = structured.model_dump()
    dumped_str = json.dumps(dumped)

    assert "SYSTEM_GROUNDING_PROMPT" not in dumped_str
    assert "You are the ABC Shield" not in dumped_str


def test_23_no_chain_of_thought_or_reasoning_exposed():
    """Structured response does not expose internal chain-of-thought or model hidden states."""
    grounded_resp = GroundedResponse(
        query="Query",
        answer="Answer",
        confidence_status="GROUNDED",
        grounded=True,
    )
    structured = StructuredResponseBuilder.build(grounded_resp)
    dumped = structured.model_dump()

    assert "chain_of_thought" not in dumped
    assert "reasoning" not in dumped
    assert "thinking" not in dumped
    assert "hidden_state" not in dumped


def test_24_generator_generate_structured_response_end_to_end():
    """GroundedGenerator.generate_structured_response integrates the full pipeline cleanly."""
    class CustomRetriever:
        def retrieve(self, *args, **kwargs):
            return [
                _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010"),
                _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance"),
            ]

    generator = GroundedGenerator(
        retriever=CustomRetriever(),
        llm_provider=MockLLMProvider(),
    )
    structured = generator.generate_structured_response(
        query="What procedures prevent bribery offences under UK law?",
        request_id="REQ-TEST-999"
    )

    assert isinstance(structured, StructuredAIResponse)
    assert structured.request_id == "REQ-TEST-999"
    assert structured.status == ResponseStatus.GROUNDED
    assert structured.grounded is True
    assert structured.gap is None
    assert len(structured.citations) == 2
    assert len(structured.provenance) == 2
    assert len(structured.conflicts) == 1
    assert structured.conflicts[0].conflict_id == "CO-001"
    assert len(structured.retrieved_evidence) == 2
    assert structured.metadata.retrieved_count == 2
    assert structured.metadata.conflict_count == 1
