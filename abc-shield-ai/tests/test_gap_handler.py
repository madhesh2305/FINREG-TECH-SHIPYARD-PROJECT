"""Automated test suite for GAP and No-Source Handling Layer (Task 7).

Verifies:
1. Empty retrieval produces NO_RETRIEVED_EVIDENCE gap, LLM is skipped, zero citations
2. Out-of-scope query (cybersecurity) produces OUT_OF_SCOPE gap without legal conclusions
3. Bribery Act top_k=3 produces MISSING_SPECIFIC_PROVISION gap referencing only retrieved chunks
4. Bribery Act top_k=5 is GROUNDED and has gap = None
5. Practical controls top_k=3 is GROUNDED and has gap = None
6. Approved-only filter on candidate dataset produces UNAPPROVED_EVIDENCE gap
7. Separation of evidence relevance, sufficiency, and approval status
8. Determinism of GAP classification across multiple calls
9. Recommended next actions are safe workflow suggestions rather than legal advice
"""

from unittest.mock import MagicMock
import pytest

from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.generation.gap_handler import GapType, GapResult, GapHandler
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


# TEST 1: Empty retrieval produces NO_RETRIEVED_EVIDENCE
def test_1_empty_retrieval_produces_no_retrieved_evidence_gap(mock_llm):
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    generator = GroundedGenerator(retriever=mock_retriever, llm_provider=mock_llm)

    res = generator.generate_response("Any query with zero results")

    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.grounded is False
    assert mock_llm.call_count == 0  # LLM skipped
    assert res.citations == []
    assert res.provenance == []

    # Gap verification
    assert res.gap is not None
    assert res.gap.is_gap is True
    assert res.gap.gap_type == GapType.NO_RETRIEVED_EVIDENCE
    assert res.gap.relevant_evidence_count == 0
    assert res.gap.approved_evidence_count == 0
    assert "not contain sufficient retrieved evidence" in res.gap.user_safe_message
    assert "source register" in res.gap.recommended_next_action.lower()


# TEST 2: Out-of-scope query (cybersecurity) produces OUT_OF_SCOPE gap
def test_2_out_of_scope_cybersecurity_produces_out_of_scope_gap(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What cybersecurity requirements apply?"

    res = generator.generate_response(query=query, top_k=3)

    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.grounded is False
    assert res.citations == []
    assert res.provenance == []

    # Gap verification
    assert res.gap is not None
    assert res.gap.is_gap is True
    assert res.gap.gap_type == GapType.OUT_OF_SCOPE
    assert "cybersecurity" in res.gap.user_safe_message.lower()
    assert "ABC Shield scope" in res.gap.user_safe_message
    # Safety: does not claim cybersecurity laws don't exist in reality
    assert "do not exist" not in res.gap.user_safe_message
    assert res.gap.relevant_evidence_count == 3
    assert res.gap.approved_evidence_count == 0  # All 3 are candidate records


# TEST 3: Specific provision absent from retrieved evidence produces MISSING_SPECIFIC_PROVISION gap
def test_3_bribery_act_top_k_3_produces_missing_specific_provision(mock_llm):
    # Scenario: Retrieved evidence contains anti-bribery guidance but lacks Section 1
    mock_retriever = MagicMock()
    mock_chunks = [
        RetrievalResult(
            chunk_id="RR-UK-07-C01",
            record_id="RR-UK-07",
            source_id="UK-07",
            regulation="How to Counter Bribery and Corruption Practice Note",
            regulator="Public Sector Fraud Authority / GOV.UK",
            jurisdiction="UK",
            section_article="Practice Note",
            title="Practical anti-bribery controls",
            text="Provides practical guidance for organisations.",
            text_type="retrieval_text",
            validation_status="Candidate - Awaiting Approval",
            is_approved_for_rag=False,
            similarity_score=0.70,
            distance=0.30,
        ),
    ]
    mock_retriever.retrieve.return_value = mock_chunks
    generator = GroundedGenerator(retriever=mock_retriever, llm_provider=mock_llm)
    query = "What does the Bribery Act 2010 say about bribing another person?"

    res = generator.generate_response(query=query, top_k=3)

    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.grounded is False
    assert res.citations == []

    # Gap verification
    assert res.gap is not None
    assert res.gap.is_gap is True
    assert res.gap.gap_type == GapType.MISSING_SPECIFIC_PROVISION
    assert "Section 1" in res.gap.user_safe_message
    # Strict safety requirement: must refer to retrieved evidence, NOT entire knowledge base
    assert "retrieved evidence" in res.gap.user_safe_message
    assert "knowledge base does not contain" not in res.gap.user_safe_message
    assert "does not exist" not in res.gap.user_safe_message


# TEST 4: Bribery Act top_k=5 is GROUNDED and has gap = None
def test_4_bribery_act_top_k_5_has_no_gap(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What does the Bribery Act 2010 say about bribing another person?"

    # At top_k=5, RR-UK-01-C01 is retrieved among the 5 candidates
    res = generator.generate_response(query=query, top_k=5)

    assert res.confidence_status == "GROUNDED"
    assert res.grounded is True
    assert "RR-UK-01-C01" in res.evidence_used

    # When grounded, there is no evidence gap
    assert res.gap is None
    # Citations and provenance from Task 6 remain intact
    assert len(res.citations) == 5
    assert len(res.provenance) == 5


# TEST 5: Practical controls top_k=3 is GROUNDED and has gap = None
def test_5_practical_controls_has_no_gap(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What are practical anti-bribery controls?"

    res = generator.generate_response(query=query, top_k=3)

    assert res.confidence_status == "GROUNDED"
    assert res.grounded is True
    assert res.gap is None
    assert len(res.citations) == 3


# TEST 6: Approved-only filter on candidate dataset produces UNAPPROVED_EVIDENCE gap
def test_6_approved_only_search_produces_unapproved_evidence_gap(persistent_retriever, mock_llm):
    generator = GroundedGenerator(retriever=persistent_retriever, llm_provider=mock_llm)
    query = "What does the Bribery Act 2010 say about bribing another person?"

    # With filter_approved_only=True, ChromaDB returns 0 records because all 15 are Candidate
    res = generator.generate_response(query=query, filter_approved_only=True)

    assert res.confidence_status == "INSUFFICIENT_EVIDENCE"
    assert res.grounded is False
    assert mock_llm.call_count == 0  # Gated before LLM

    # Gap verification
    assert res.gap is not None
    assert res.gap.is_gap is True
    assert res.gap.gap_type == GapType.UNAPPROVED_EVIDENCE
    assert "Candidate - Awaiting Approval" in res.gap.message
    assert "approved" in res.gap.user_safe_message.lower()
    assert "SME approval" in res.gap.recommended_next_action


# TEST 7: Separation of evidence relevance, sufficiency, and approval status
def test_7_separation_of_relevance_sufficiency_and_approval():
    candidate_chunk = RetrievalResult(
        chunk_id="RR-CAND-01-C01",
        record_id="RR-CAND-01",
        source_id="CAND-01",
        regulation="Anti-Bribery Standard",
        regulator="Test Regulator",
        jurisdiction="UK",
        section_article="General Principles",
        title="General Anti-Bribery Principles",
        text="General high-level overview text without specific rules.",
        text_type="requirement_paraphrase",
        validation_status="Candidate - Awaiting Approval",
        is_approved_for_rag=False,  # Unapproved
        similarity_score=0.80,
        distance=0.20,
    )

    gap = GapHandler.analyze_gap(
        query="What specific penalty applies for bribery?",
        retrieved_chunks=[candidate_chunk],
        is_grounded=False,
    )

    assert gap is not None
    # Sufficient/insufficient determination is independent of approval
    assert gap.relevant_evidence_count == 1
    assert gap.approved_evidence_count == 0
    assert gap.gap_type in (GapType.INSUFFICIENT_RETRIEVED_EVIDENCE, GapType.MISSING_SPECIFIC_PROVISION)


# TEST 8: Determinism of GAP classification
def test_8_gap_classification_is_deterministic(persistent_retriever):
    retrieved = persistent_retriever.retrieve("What does the Bribery Act 2010 say about bribing another person?", top_k=3)

    gap1 = GapHandler.analyze_gap("What does the Bribery Act 2010 say about bribing another person?", retrieved, is_grounded=False)
    gap2 = GapHandler.analyze_gap("What does the Bribery Act 2010 say about bribing another person?", retrieved, is_grounded=False)

    assert gap1 == gap2
    assert gap1.gap_type == gap2.gap_type
    assert gap1.user_safe_message == gap2.user_safe_message
    assert gap1.recommended_next_action == gap2.recommended_next_action


# TEST 9: Recommended next actions are safe workflow suggestions rather than legal advice
def test_9_recommended_actions_are_workflow_suggestions():
    # Out of scope
    mock_chunk = MagicMock(chunk_id="C1", record_id="R1", is_approved_for_rag=False)
    gap_oos = GapHandler.analyze_gap("What are the sanctions requirements?", [mock_chunk], is_grounded=False)
    assert "Refer to an approved knowledge source" in gap_oos.recommended_next_action
    assert "legal" not in gap_oos.recommended_next_action.lower()

    # Zero retrieval
    gap_zero = GapHandler.analyze_gap("Random query", [], is_grounded=False)
    assert "source register" in gap_zero.recommended_next_action.lower()
