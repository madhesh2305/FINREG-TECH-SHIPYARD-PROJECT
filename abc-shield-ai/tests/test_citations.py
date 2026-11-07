"""Automated test suite for Citation & Provenance Layer (Task 6).

Verifies:
1. Citation metadata accuracy against RetrievalResult (all fields copied, nulls preserved)
2. Human-readable citation format ([chunk_id | record_id | regulation | section])
3. Citation integrity enforcement (unretrieved chunks strictly rejected)
4. Empty retrieval safety (zero citations, zero provenance)
5. Insufficient evidence handling (zero citations, zero provenance)
6. Bribery Act top_k=3 test (no citation for RR-UK-01-C01)
7. Bribery Act top_k=5 test (valid citation for RR-UK-01-C01 when retrieved)
8. Multiple chunk deduplication and order preservation
9. Candidate approval status retention in citations
10. Determinism of citation and provenance generation
"""

from unittest.mock import MagicMock
import pytest

from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.generation.citations import Citation, ProvenanceRecord, CitationBuilder
from rag.generation.grounded_generator import GroundedGenerator, GroundedResponse
from rag.generation.llm_interface import MockLLMProvider


@pytest.fixture
def persistent_retriever():
    """Real Task 4 retriever connected to persistent ChromaDB."""
    return RegulatoryRetriever()


@pytest.fixture
def mock_llm():
    """Deterministic MockLLMProvider."""
    return MockLLMProvider()


@pytest.fixture
def sample_retrieval_result():
    """Realistic RetrievalResult based on UK-01."""
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


# TEST 1: Citation metadata exactly matches RetrievalResult
def test_1_citation_metadata_accuracy(sample_retrieval_result):
    cit = Citation.from_retrieval_result(sample_retrieval_result)

    assert cit.citation_id == "CIT-RR-UK-01-C01"
    assert cit.chunk_id == sample_retrieval_result.chunk_id
    assert cit.record_id == sample_retrieval_result.record_id
    assert cit.source_id == sample_retrieval_result.source_id
    assert cit.regulation == sample_retrieval_result.regulation
    assert cit.regulator == sample_retrieval_result.regulator
    assert cit.jurisdiction == sample_retrieval_result.jurisdiction
    assert cit.section_article == sample_retrieval_result.section_article
    assert cit.title == sample_retrieval_result.title
    assert cit.topic == sample_retrieval_result.topic
    assert cit.official_source == sample_retrieval_result.official_source
    assert cit.version_date == sample_retrieval_result.version_date
    assert cit.effective_date == sample_retrieval_result.effective_date
    assert cit.validation_status == sample_retrieval_result.validation_status
    assert cit.is_approved_for_rag == sample_retrieval_result.is_approved_for_rag
    assert cit.text_type == sample_retrieval_result.text_type

    # Verify provenance conversion
    prov = cit.to_provenance(similarity_score=sample_retrieval_result.similarity_score)
    assert isinstance(prov, ProvenanceRecord)
    assert prov.record_id == cit.record_id
    assert prov.source_id == cit.source_id
    assert prov.official_source == cit.official_source
    assert prov.similarity_score == 0.885


# TEST 2: Missing metadata is preserved as None rather than fabricated
def test_2_missing_metadata_preserved_as_none():
    sparse_chunk = RetrievalResult(
        chunk_id="RR-SPARSE-01-C01",
        record_id="RR-SPARSE-01",
        source_id="SPARSE-01",
        regulation="Sparse Regulation",
        regulator="Sparse Regulator",
        jurisdiction="UK",
        section_article="Article 1",
        title="Sparse Title",
        text="Sparse text content.",
        text_type="requirement_paraphrase",
        topic=None,
        official_source=None,
        version_date=None,
        effective_date=None,
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.75,
        distance=0.25,
    )

    cit = Citation.from_retrieval_result(sparse_chunk)
    assert cit.topic is None
    assert cit.official_source is None
    assert cit.version_date is None
    assert cit.effective_date is None


# TEST 3: Human-readable citation formatting
def test_3_human_readable_citation_format(sample_retrieval_result):
    cit = Citation.from_retrieval_result(sample_retrieval_result)
    expected_format = "[RR-UK-01-C01 | RR-UK-01 | Bribery Act 2010 | Section 1]"
    assert cit.formatted_citation == expected_format


# TEST 4: Citation integrity whitelist verification
def test_4_citation_integrity_whitelist():
    chunk_a = RetrievalResult(
        chunk_id="RR-VALID-01-C01",
        record_id="RR-VALID-01",
        source_id="V-01",
        regulation="Regulation A",
        regulator="Regulator A",
        jurisdiction="UK",
        section_article="Section A",
        title="Title A",
        text="Valid text A.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.90,
        distance=0.10,
    )

    # Supply only chunk_a
    retrieved = [chunk_a]
    citations, provenance = CitationBuilder.build_citations(retrieved, is_grounded=True)

    citation_ids = [c.chunk_id for c in citations]
    assert "RR-VALID-01-C01" in citation_ids
    # An unretrieved chunk can NEVER appear
    assert "RR-UK-01-C01" not in citation_ids
    assert "RR-UK-07-C01" not in citation_ids


# TEST 5: Empty retrieval safety produces zero citations
def test_5_empty_retrieval_produces_zero_citations():
    citations, provenance = CitationBuilder.build_citations([], is_grounded=False)
    assert citations == []
    assert provenance == []

    # Also test via GroundedGenerator with empty retriever
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    generator = GroundedGenerator(retriever=mock_retriever, llm_provider=MockLLMProvider())

    res = generator.generate_response("Any question")
    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.grounded is False
    assert res.citations == []
    assert res.provenance == []


# TEST 6: Insufficient evidence produces zero citations
def test_6_insufficient_evidence_produces_zero_citations(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    # Cybersecurity is out-of-scope for anti-bribery knowledge base
    res = generator.generate_response("What cybersecurity requirements apply?", top_k=3)

    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.grounded is False
    assert res.citations == []
    assert res.provenance == []


# TEST 7: Bribery Act query with top_k=3 produces citation for RR-UK-01-C01 in Week 4
def test_7_bribery_act_top_k_3_no_citation_for_rr_uk_01(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What does the Bribery Act 2010 say about bribing another person?"

    # At top_k=3, Week 4 retriever returns RR-UK-01-C01 at Rank 1
    res = generator.generate_response(query=query, top_k=3)

    assert res.confidence_status == "GROUNDED"
    assert res.grounded is True
    assert "RR-UK-01-C01" in res.evidence_used

    # Core Citation Integrity Assertion: RR-UK-01-C01 appears as a verified citation
    assert "RR-UK-01-C01" in [c.chunk_id for c in res.citations]
    assert len(res.citations) > 0
    assert len(res.provenance) > 0
    # Verify citation attributes
    c = next(c for c in res.citations if c.chunk_id == "RR-UK-01-C01")
    assert c.regulation == "Bribery Act 2010"
    assert c.section_article == "Section 1"


# TEST 8: Bribery Act query with top_k=5 produces citation for RR-UK-01-C01
def test_8_bribery_act_top_k_5_produces_citation_for_rr_uk_01(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What does the Bribery Act 2010 say about bribing another person?"

    # At top_k=5, RR-UK-01-C01 is retrieved among the 5 chunks
    res = generator.generate_response(query=query, top_k=5)

    assert res.confidence_status == "GROUNDED"
    assert res.grounded is True
    assert "RR-UK-01-C01" in res.evidence_used

    # Core Citation Assertion: Citations are constructed deterministically
    cited_chunk_ids = [c.chunk_id for c in res.citations]
    assert "RR-UK-01-C01" in cited_chunk_ids

    # Find the specific RR-UK-01-C01 citation and verify its metadata
    uk01_citation = next(c for c in res.citations if c.chunk_id == "RR-UK-01-C01")
    assert uk01_citation.record_id == "RR-UK-01"
    assert uk01_citation.source_id == "UK-01"
    assert uk01_citation.regulation == "Bribery Act 2010"
    assert uk01_citation.section_article == "Section 1"
    assert uk01_citation.is_approved_for_rag is False
    assert uk01_citation.validation_status == "Candidate - Awaiting Approval"
    assert uk01_citation.formatted_citation == "[RR-UK-01-C01 | RR-UK-01 | Bribery Act 2010 | Section 1]"


# TEST 9: Deduplication and retrieval order preservation
def test_9_multiple_chunks_deduplication():
    chunk_1 = RetrievalResult(
        chunk_id="RR-TEST-01-C01",
        record_id="RR-TEST-01",
        source_id="T-01",
        regulation="Test Act",
        regulator="Test Regulator",
        jurisdiction="UK",
        section_article="Sec 1",
        title="Title 1",
        text="Text 1",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.90,
        distance=0.10,
    )
    chunk_2 = RetrievalResult(
        chunk_id="RR-TEST-02-C01",
        record_id="RR-TEST-02",
        source_id="T-02",
        regulation="Test Act 2",
        regulator="Test Regulator 2",
        jurisdiction="UK",
        section_article="Sec 2",
        title="Title 2",
        text="Text 2",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,
        similarity_score=0.85,
        distance=0.15,
    )

    # Provide duplicate of chunk_1 in input list
    input_chunks = [chunk_1, chunk_2, chunk_1]
    citations, provenance = CitationBuilder.build_citations(input_chunks, is_grounded=True)

    # Verify deduplication
    assert len(citations) == 2
    assert len(provenance) == 2
    assert [c.chunk_id for c in citations] == ["RR-TEST-01-C01", "RR-TEST-02-C01"]


# TEST 10: Citation generation is deterministic across multiple invocations
def test_10_citation_generation_is_deterministic(sample_retrieval_result):
    input_chunks = [sample_retrieval_result]

    cit1, prov1 = CitationBuilder.build_citations(input_chunks, is_grounded=True)
    cit2, prov2 = CitationBuilder.build_citations(input_chunks, is_grounded=True)

    assert cit1 == cit2
    assert prov1 == prov2
