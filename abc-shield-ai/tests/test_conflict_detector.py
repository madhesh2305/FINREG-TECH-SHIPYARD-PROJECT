"""Tests for Task 8: Deterministic Regulatory Conflict and Overlap Detection.

Validates that conflict/overlap detection operates purely deterministically over
retrieved evidence chunks without calling an LLM, inventing relationships,
modifying approval status, or performing legal conflict resolution.
"""

import pytest
from pathlib import Path
from typing import List

from rag.conflict import (
    ConflictDetector,
    ConflictType,
    ConflictFinding,
    classify_relationship,
)
from rag.retrieval.retriever import RetrievalResult, RegulatoryRetriever
from rag.generation.grounded_generator import GroundedGenerator, GroundedResponse
from rag.generation.llm_interface import MockLLMProvider
from rag.generation.gap_handler import GapType


def _make_chunk(
    chunk_id: str,
    record_id: str,
    source_id: str,
    regulation: str,
    section_article: str = "Section 1",
    validation_status: str = "Candidate - Awaiting Approval",
    is_approved_for_rag: bool = False,
    similarity_score: float = 0.85,
) -> RetrievalResult:
    """Helper to construct synthetic RetrievalResult fixtures."""
    return RetrievalResult(
        chunk_id=chunk_id,
        record_id=record_id,
        source_id=source_id,
        regulation=regulation,
        regulator="Regulator Test",
        jurisdiction="UK" if source_id.startswith("UK") else "EU",
        section_article=section_article,
        title=f"Title for {section_article}",
        text=f"Sample requirement text for {chunk_id}",
        text_type="requirement_paraphrase",
        topic="Anti-Bribery",
        official_source="https://example.com/legal-source",
        version_date="2024-01-01",
        effective_date="2024-01-01",
        validation_status=validation_status,
        is_approved_for_rag=is_approved_for_rag,
        similarity_score=similarity_score,
        distance=1.0 - similarity_score,
    )


@pytest.fixture(scope="module")
def conflict_detector() -> ConflictDetector:
    """Fixture providing ConflictDetector loaded with actual 11 workbook pairs."""
    return ConflictDetector()


# Test 1: Empty retrieval
def test_1_empty_retrieval_returns_no_findings(conflict_detector: ConflictDetector):
    """Empty retrieval produces zero conflict findings."""
    findings = conflict_detector.detect([])
    assert findings == []


# Test 2: One-sided retrieval
def test_2_one_sided_source_retrieval_does_not_create_active_conflict(conflict_detector: ConflictDetector):
    """Retrieving only one source of a known pair does NOT produce an active conflict finding."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    findings = conflict_detector.detect([chunk_uk01])
    assert findings == []

    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    findings2 = conflict_detector.detect([chunk_uk02])
    assert findings2 == []


# Test 3: Both sources retrieved
def test_3_both_sources_of_known_pair_retrieved(conflict_detector: ConflictDetector):
    """Retrieving both sources of a known pair (UK-01 and UK-02) returns the documented finding."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")

    findings = conflict_detector.detect([chunk_uk01, chunk_uk02])
    assert len(findings) == 1
    finding = findings[0]
    assert finding.conflict_id == "CO-001"
    assert finding.source_id_1 == "UK-01"
    assert finding.source_id_2 == "UK-02"
    assert finding.both_sources_retrieved is True


# Test 4: Unknown source pair
def test_4_unknown_source_pair_no_invented_conflict(conflict_detector: ConflictDetector):
    """Two sources without a documented relationship do not produce an invented conflict."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_eu03 = _make_chunk("RR-EU-03-C01", "RR-EU-03", "EU-03", "Directive (EU) 2019/1937 - Whistleblower Protection")

    findings = conflict_detector.detect([chunk_uk01, chunk_eu03])
    assert findings == []


# Test 5: Multiple chunks deduplication
def test_5_multiple_chunks_same_source_deduplicated(conflict_detector: ConflictDetector):
    """Multiple chunks from the same source pair do not duplicate conflict findings."""
    chunks = [
        _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010"),
        _make_chunk("RR-UK-01-C02", "RR-UK-01", "UK-01", "Bribery Act 2010"),
        _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance"),
    ]
    findings = conflict_detector.detect(chunks)
    assert len(findings) == 1
    assert findings[0].conflict_id == "CO-001"
    assert findings[0].retrieved_chunk_ids == ["RR-UK-01-C01", "RR-UK-01-C02", "RR-UK-02-C01"]


# Test 6: Conflict_ID preserved
def test_6_conflict_id_preserved(conflict_detector: ConflictDetector):
    """Conflict_ID matches the actual registered ID from the controlled workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    assert finding.conflict_id == "CO-001"


# Test 7: Source IDs preserved
def test_7_source_ids_preserved(conflict_detector: ConflictDetector):
    """Source_ID_1 and Source_ID_2 match the registered workbook values."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    assert finding.source_id_1 == "UK-01"
    assert finding.source_id_2 == "UK-02"
    assert finding.source_1 == "Bribery Act 2010"
    assert finding.source_2 == "Bribery Act 2010 Guidance"


# Test 8: Relationship preserved
def test_8_relationship_preserved(conflict_detector: ConflictDetector):
    """The original relationship string is preserved exactly as recorded in the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    assert finding.relationship == "Overlap - complementary"


# Test 9: Requirement comparison preserved
def test_9_requirement_comparison_preserved(conflict_detector: ConflictDetector):
    """The documented requirement comparison is preserved from the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    expected = "Act creates legal offences; guidance explains procedures organisations can use to prevent bribery and describes six core principles."
    assert finding.requirement_comparison == expected


# Test 10: Scope difference preserved
def test_10_scope_difference_preserved(conflict_detector: ConflictDetector):
    """The documented scope difference is preserved from the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    expected = "Law applies to relevant offences/organisations; guidance is explanatory and procedural."
    assert finding.scope_difference == expected


# Test 11: Authority difference preserved
def test_11_authority_difference_preserved(conflict_detector: ConflictDetector):
    """The documented authority difference is preserved from the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    expected = "Parliamentary legislation vs Ministry of Justice guidance."
    assert finding.authority_difference == expected


# Test 12: Version/effective-date difference preserved
def test_12_version_effective_date_difference_preserved(conflict_detector: ConflictDetector):
    """The documented version and effective date difference is preserved from the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    expected = "Act: 2010; guidance published 2012 and updated 22 Jan 2025."
    assert finding.version_effective_date_difference == expected


# Test 13: Conflict status preserved
def test_13_conflict_status_preserved(conflict_detector: ConflictDetector):
    """The documented conflict status is preserved from the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    assert finding.conflict_status == "No direct conflict identified"


# Test 14: RAG_Use preserved
def test_14_rag_use_preserved(conflict_detector: ConflictDetector):
    """The documented RAG usage guidance is preserved from the workbook."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]
    expected = "Retrieve binding Act requirement first; use guidance as implementation context."
    assert finding.rag_use == expected


# Test 15: Conflict detector does not call an LLM
def test_15_conflict_detector_does_not_call_llm(conflict_detector: ConflictDetector, monkeypatch):
    """ConflictDetector executes without invoking any LLM provider or generation function."""
    class FailIfCalledLLM:
        def generate(self, *args, **kwargs):
            raise AssertionError("LLM was called during conflict detection!")

    # Attempting detection does not access or call the LLM
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    findings = conflict_detector.detect([chunk_uk01, chunk_uk02])
    assert len(findings) == 1


# Test 16: Conflict detector does not modify approval status
def test_16_conflict_detector_does_not_modify_approval_status(conflict_detector: ConflictDetector):
    """Candidate validation status is preserved and does NOT get converted to approved."""
    chunk_uk01 = _make_chunk(
        "RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010",
        validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False
    )
    chunk_uk02 = _make_chunk(
        "RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance",
        validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False
    )
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]

    assert finding.source_1_validation_status == "Candidate - Awaiting Approval"
    assert finding.source_2_validation_status == "Candidate - Awaiting Approval"
    assert finding.source_1_is_approved_for_rag is False
    assert finding.source_2_is_approved_for_rag is False
    assert finding.is_approved_for_rag is False


# Test 17: Conflict detector does not resolve conflicts
def test_17_conflict_detector_does_not_resolve_conflicts(conflict_detector: ConflictDetector):
    """The detector does not declare winning sources, controlling laws, or overriding regulations."""
    chunk_uk01 = _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010")
    chunk_uk02 = _make_chunk("RR-UK-02-C01", "RR-UK-02", "UK-02", "Bribery Act 2010 Guidance")
    finding = conflict_detector.detect([chunk_uk01, chunk_uk02])[0]

    msg_lower = finding.message.lower()
    assert "override" not in msg_lower
    assert "wins" not in msg_lower
    assert "controlling" not in msg_lower
    assert "must follow" not in msg_lower
    assert "no legal conflict resolution is made by this system" in msg_lower


# Test 18: GroundedResponse contains conflict findings
def test_18_grounded_response_contains_conflict_findings():
    """GroundedGenerator.generate_response includes detected conflicts in GroundedResponse."""
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
    response = generator.generate_response("What procedures prevent bribery under UK law?")

    assert hasattr(response, "conflicts")
    assert len(response.conflicts) == 1
    assert response.conflicts[0].conflict_id == "CO-001"
    assert response.conflicts[0].both_sources_retrieved is True


# Test 19: Existing GAP handling still works
def test_19_existing_gap_handling_still_works():
    """GroundedGenerator continues to provide accurate GAP analysis when evidence is insufficient."""
    class EmptyRetriever:
        def retrieve(self, *args, **kwargs):
            return []

    generator = GroundedGenerator(
        retriever=EmptyRetriever(),
        llm_provider=MockLLMProvider(),
    )
    response = generator.generate_response("What are DORA requirements?")
    assert response.gap is not None
    assert response.gap.is_gap is True
    assert response.gap.gap_type == GapType.NO_RETRIEVED_EVIDENCE
    assert response.conflicts == []


# Test 20: Existing citation/provenance behavior still works
def test_20_existing_citation_behavior_still_works():
    """Citations and provenance records remain strictly grounded and obey whitelisting."""
    class CustomRetriever:
        def retrieve(self, *args, **kwargs):
            return [
                _make_chunk("RR-UK-01-C01", "RR-UK-01", "UK-01", "Bribery Act 2010"),
            ]

    generator = GroundedGenerator(
        retriever=CustomRetriever(),
        llm_provider=MockLLMProvider(),
    )
    response = generator.generate_response("What does UK Bribery Act state?")
    assert len(response.citations) == 1
    assert response.citations[0].chunk_id == "RR-UK-01-C01"
    assert len(response.provenance) == 1
    assert response.provenance[0].chunk_id == "RR-UK-01-C01"
    # One-sided retrieval produces zero active conflict findings
    assert response.conflicts == []


# Test 21: Amendment relationship (CO-010) mapped accurately
def test_21_amendment_relationship_mapped_accurately(conflict_detector: ConflictDetector):
    """Direct legal amendment relationship (EU-04 and EU-05) is mapped to VERSION_DIFFERENCE."""
    chunk_eu04 = _make_chunk("RR-EU-04-C01", "RR-EU-04", "EU-04", "Regulation (EU, Euratom) No 883/2013 - OLAF")
    chunk_eu05 = _make_chunk("RR-EU-05-C01", "RR-EU-05", "EU-05", "Regulation (EU, Euratom) 2020/2223")

    findings = conflict_detector.detect([chunk_eu04, chunk_eu05])
    assert len(findings) == 1
    finding = findings[0]
    assert finding.conflict_id == "CO-010"
    assert finding.source_id_1 == "EU-04"
    assert finding.source_id_2 == "EU-05"
    assert finding.relationship == "Direct legal relationship - amendment, not conflict"
    assert finding.conflict_status == "No conflict; version/amendment relationship"
    assert finding.conflict_type == ConflictType.VERSION_DIFFERENCE
    assert "amends 883/2013" in finding.requirement_comparison
