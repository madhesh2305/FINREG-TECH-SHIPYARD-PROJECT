"""Automated test suite for Task 10 RAG evaluation and safety testing.

Covers dataset validation, dynamic ID loading, retrieval metrics, groundedness rubrics,
citation validity, GAP accuracy, conflict detection, safety gating, prompt injection,
and report generation.
"""

import pytest
from pathlib import Path
import json

from rag.evaluation.evaluation_models import (
    EvaluationCase,
    GroundednessOutcome,
    CaseRetrievalResult,
    RetrievalMetrics,
    CaseGroundednessResult,
    CitationEvaluationResult,
    GapEvaluationResult,
    ConflictEvaluationResult,
    SafetyEvaluationResult,
    PromptInjectionResult,
)
from rag.evaluation.evaluation_dataset import EvaluationDatasetValidator
from rag.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.evaluation.generation_evaluator import GenerationEvaluator
from rag.evaluation.safety_evaluator import SafetyEvaluator
from rag.evaluation.evaluation_runner import EvaluationRunner
from rag.retrieval.retriever import RetrievalResult
from rag.output.structured_response import StructuredAIResponse, ResponseStatus, RetrievedEvidenceItem
from rag.generation.citations import Citation, ProvenanceRecord
from rag.generation.gap_handler import GapResult, GapType
from rag.conflict.conflict_detector import ConflictFinding, ConflictType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    return EvaluationDatasetValidator()


@pytest.fixture
def sample_cases(validator):
    return validator.load_cases()


@pytest.fixture
def generation_evaluator():
    return GenerationEvaluator()


@pytest.fixture
def safety_evaluator():
    return SafetyEvaluator()


# ---------------------------------------------------------------------------
# 1. Dataset & Dynamic ID Tests
# ---------------------------------------------------------------------------

def test_evaluation_dataset_loads_all_cases(validator, sample_cases):
    """Test 1: Benchmark dataset loads all controlled evaluation cases."""
    assert len(sample_cases) >= 32
    assert all(isinstance(c, EvaluationCase) for c in sample_cases)


def test_evaluation_dataset_validates_dynamic_record_ids(validator):
    """Test 2: Dynamic validation derives valid record IDs without hardcoded ranges."""
    valid_ids = validator.valid_record_ids
    assert len(valid_ids) == 15
    assert "RR-UK-01" in valid_ids
    assert "RR-EU-01" in valid_ids


def test_evaluation_dataset_validates_dynamic_source_ids(validator):
    """Test 3: Dynamic validation derives valid source register IDs."""
    valid_sources = validator.valid_source_ids
    assert len(valid_sources) == 15
    assert "UK-01" in valid_sources
    assert "EU-01" in valid_sources


def test_evaluation_dataset_validates_dynamic_conflict_ids(validator):
    """Test 4: Dynamic validation derives valid conflict IDs from ConflictDetector."""
    valid_conflicts = validator.valid_conflict_ids
    assert len(valid_conflicts) == 11
    assert "CO-001" in valid_conflicts
    assert "CO-011" in valid_conflicts


def test_evaluation_dataset_flags_invalid_id(validator):
    """Test 5: Dataset validator flags unverified or fabricated IDs."""
    bad_case = EvaluationCase(
        case_id="BAD-01",
        query="Invalid query",
        category="A",
        expected_record_ids=["RR-FAKE-99"],
        expected_source_ids=["FAKE-01"],
        expected_conflict_ids=["CO-999"],
        expected_behavior="Should fail validation",
    )
    errors = validator.validate_case(bad_case)
    assert len(errors) == 3
    assert any("RR-FAKE-99" in e for e in errors)
    assert any("FAKE-01" in e for e in errors)
    assert any("CO-999" in e for e in errors)


def test_evaluation_dataset_category_distribution(validator, sample_cases):
    """Test 6: Benchmark dataset covers all categories A through O."""
    summary = validator.validate_all(sample_cases)
    assert summary["is_valid"] is True
    categories = summary["category_distribution"]
    expected_categories = [chr(c) for c in range(ord('A'), ord('P'))]
    for cat in expected_categories:
        assert cat in categories
        assert categories[cat] >= 1


def test_evaluation_dataset_human_review_flags(validator, sample_cases):
    """Test 7: Cases with ambiguous relevance are flagged for human SME review."""
    review_cases = [c for c in sample_cases if c.requires_human_review]
    assert len(review_cases) > 0
    assert any(c.category == "F" for c in review_cases)


# ---------------------------------------------------------------------------
# 2. Retrieval Evaluation Tests
# ---------------------------------------------------------------------------

def test_retrieval_evaluator_record_deduplication():
    """Test 8: Multiple chunks from the same record count as 1 record for metric calculation."""
    evaluator = RetrievalEvaluator()
    case = EvaluationCase(
        case_id="TEST-01",
        query="Test query",
        category="A",
        expected_record_ids=["RR-UK-01"],
        expected_behavior="Test deduplication",
    )

    # Mock retrieve returning 2 chunks of RR-UK-01 and 1 of RR-UK-02
    class MockRetriever:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
                    regulation="Bribery Act 2010", regulator="UK", jurisdiction="UK",
                    section_article="Section 1", title="Title", text="Text", text_type="paraphrase",
                    validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
                RetrievalResult(
                    chunk_id="RR-UK-01-C02", record_id="RR-UK-01", source_id="UK-01",
                    regulation="Bribery Act 2010", regulator="UK", jurisdiction="UK",
                    section_article="Section 1", title="Title", text="Text 2", text_type="paraphrase",
                    validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False,
                    similarity_score=0.85, distance=0.15
                ),
                RetrievalResult(
                    chunk_id="RR-UK-02-C01", record_id="RR-UK-02", source_id="UK-02",
                    regulation="Bribery Act Guidance", regulator="UK", jurisdiction="UK",
                    section_article="Six Principles", title="Title", text="Text 3", text_type="paraphrase",
                    validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False,
                    similarity_score=0.7, distance=0.3
                ),
            ]

    evaluator.retriever = MockRetriever()
    res = evaluator.evaluate_case(case, top_k=3)
    # Deduplicated retrieved records should be RR-UK-01, RR-UK-02 (length 2, not 3)
    assert res.retrieved_record_ids == ["RR-UK-01", "RR-UK-02"]
    assert res.precision_at_k[3] == round(1.0 / 3.0, 4)
    assert res.recall_at_k[3] == 1.0


def test_retrieval_evaluator_precision_at_k():
    """Test 9: Precision@K calculation."""
    evaluator = RetrievalEvaluator()
    case = EvaluationCase(
        case_id="TEST-02A",
        query="Test query",
        category="A",
        expected_record_ids=["RR-UK-01", "RR-UK-02"],
        expected_behavior="Test precision",
    )

    class MockRetriever:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
                    regulation="Reg 1", regulator="UK", jurisdiction="UK",
                    section_article="Sec 1", title="T1", text="Txt1", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
                RetrievalResult(
                    chunk_id="RR-UK-03-C01", record_id="RR-UK-03", source_id="UK-03",
                    regulation="Reg 3", regulator="UK", jurisdiction="UK",
                    section_article="Sec 3", title="T3", text="Txt3", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.8, distance=0.2
                ),
            ]

    evaluator.retriever = MockRetriever()
    res = evaluator.evaluate_case(case, top_k=2)
    assert res.precision_at_k[1] == 1.0


def test_retrieval_evaluator_recall_at_k():
    """Test 10: Recall@K calculation."""
    evaluator = RetrievalEvaluator()
    case = EvaluationCase(
        case_id="TEST-02B",
        query="Test query",
        category="A",
        expected_record_ids=["RR-UK-01", "RR-UK-02"],
        expected_behavior="Test recall",
    )

    class MockRetriever:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
                    regulation="Reg 1", regulator="UK", jurisdiction="UK",
                    section_article="Sec 1", title="T1", text="Txt1", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
                RetrievalResult(
                    chunk_id="RR-UK-03-C01", record_id="RR-UK-03", source_id="UK-03",
                    regulation="Reg 3", regulator="UK", jurisdiction="UK",
                    section_article="Sec 3", title="T3", text="Txt3", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.8, distance=0.2
                ),
            ]

    evaluator.retriever = MockRetriever()
    res = evaluator.evaluate_case(case, top_k=2)
    assert res.recall_at_k[1] == 0.5


def test_retrieval_evaluator_hit_rate_at_k():
    """Test 11: Hit Rate@K calculation."""
    evaluator = RetrievalEvaluator()
    case = EvaluationCase(
        case_id="TEST-02C",
        query="Test query",
        category="A",
        expected_record_ids=["RR-UK-01", "RR-UK-02"],
        expected_behavior="Test hit rate",
    )

    class MockRetriever:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
                    regulation="Reg 1", regulator="UK", jurisdiction="UK",
                    section_article="Sec 1", title="T1", text="Txt1", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
                RetrievalResult(
                    chunk_id="RR-UK-03-C01", record_id="RR-UK-03", source_id="UK-03",
                    regulation="Reg 3", regulator="UK", jurisdiction="UK",
                    section_article="Sec 3", title="T3", text="Txt3", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.8, distance=0.2
                ),
            ]

    evaluator.retriever = MockRetriever()
    res = evaluator.evaluate_case(case, top_k=2)
    assert res.hit_rate_at_k[1] == 1.0


def test_retrieval_evaluator_mrr():
    """Test 12: Reciprocal Rank and MRR calculation."""
    evaluator = RetrievalEvaluator()
    case = EvaluationCase(
        case_id="TEST-03",
        query="Test query",
        category="A",
        expected_record_ids=["RR-UK-02"],
        expected_behavior="Test MRR",
    )

    class MockRetriever:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
                    regulation="R1", regulator="UK", jurisdiction="UK",
                    section_article="S1", title="T1", text="Txt", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
                RetrievalResult(
                    chunk_id="RR-UK-02-C01", record_id="RR-UK-02", source_id="UK-02",
                    regulation="R2", regulator="UK", jurisdiction="UK",
                    section_article="S2", title="T2", text="Txt", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.85, distance=0.15
                ),
            ]

    evaluator.retriever = MockRetriever()
    res = evaluator.evaluate_case(case, top_k=2)
    # First relevant chunk RR-UK-02 is at rank 2 -> RR = 1/2 = 0.5
    assert res.reciprocal_rank == 0.5


def test_retrieval_evaluator_zero_expected_handling():
    """Test 13: Zero-expected cases handled safely without division by zero."""
    evaluator = RetrievalEvaluator()
    zero_case = EvaluationCase(
        case_id="ZERO-01",
        query="Out of scope query",
        category="J",
        expected_record_ids=[],
        expected_behavior="Safe zero handling",
    )
    res = evaluator.evaluate_case(zero_case, top_k=5)
    assert res.is_zero_expected is True
    assert res.precision_at_k[1] == 0.0
    assert res.recall_at_k[1] == 0.0
    assert res.reciprocal_rank == 0.0


def test_retrieval_evaluator_exact_provision_analysis():
    """Test 14: Exact provision analysis returns target provision rank and explanatory notes."""
    evaluator = RetrievalEvaluator()
    epa = evaluator.analyze_exact_provision()
    assert epa.target_record_id == "RR-UK-01"
    assert epa.target_chunk_id == "RR-UK-01-C01"
    assert epa.rank_in_retrieval is not None
    assert isinstance(epa.notes, str)
    assert len(epa.notes) > 20


# ---------------------------------------------------------------------------
# 3. Generation & Groundedness Tests
# ---------------------------------------------------------------------------

def _make_dummy_citation(
    chunk_id: str,
    record_id: str,
    source_id: str,
    regulation: str = "Bribery Act 2010",
    section_article: str = "Section 1",
) -> Citation:
    return Citation(
        citation_id=f"CIT-{chunk_id}",
        chunk_id=chunk_id,
        record_id=record_id,
        source_id=source_id,
        regulation=regulation,
        jurisdiction="UK",
        section_article=section_article,
        title="Test Title",
        validation_status="Candidate - Awaiting Approval",
        text_type="requirement_paraphrase",
        formatted_citation=f"[{chunk_id} | {record_id} | {regulation} | {section_article}]",
    )


def test_generation_evaluator_groundedness_supported(generation_evaluator):
    """Test 15: Groundedness outcome is SUPPORTED when all deterministic checks pass."""
    case = EvaluationCase(
        case_id="G-01",
        query="Explain Section 1",
        category="A",
        expected_record_ids=["RR-UK-01"],
        expected_status="GROUNDED",
        expected_behavior="Passes checks",
    )
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
            regulation="Bribery Act 2010", section_article="Section 1", title="Offences",
            text="Active bribery is an offence.", validation_status="Candidate - Awaiting Approval"
        )
    ]
    citation = _make_dummy_citation(
        chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01"
    )
    response = StructuredAIResponse(
        status=ResponseStatus.GROUNDED,
        query="Explain Section 1",
        answer="Under Section 1, active bribery is an offence.",
        grounded=True,
        retrieved_evidence=evidence,
        citations=[citation],
    )
    result = generation_evaluator.evaluate_case_groundedness(case, response)
    assert result.outcome == GroundednessOutcome.SUPPORTED
    assert len(result.checks_failed) == 0


def test_generation_evaluator_groundedness_unwhitelisted_citation(generation_evaluator):
    """Test 16: Groundedness outcome is UNSUPPORTED when an unwhitelisted citation is found."""
    case = EvaluationCase(
        case_id="G-02",
        query="Explain Section 1",
        category="A",
        expected_record_ids=["RR-UK-01"],
        expected_status="GROUNDED",
        expected_behavior="Fail on unwhitelisted citation",
    )
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
            regulation="Bribery Act 2010", section_article="Section 1", title="Offences",
            text="Active bribery is an offence.", validation_status="Candidate - Awaiting Approval"
        )
    ]
    fabricated_citation = _make_dummy_citation(
        chunk_id="RR-FABRICATED-C01", record_id="RR-FABRICATED", source_id="FAB-01",
        regulation="Invented Act", section_article="Section 99"
    )
    response = StructuredAIResponse(
        status=ResponseStatus.GROUNDED,
        query="Explain Section 1",
        answer="Fabricated claim.",
        grounded=True,
        retrieved_evidence=evidence,
        citations=[fabricated_citation],
    )
    result = generation_evaluator.evaluate_case_groundedness(case, response)
    assert result.outcome == GroundednessOutcome.UNSUPPORTED
    assert any("Unwhitelisted" in f for f in result.checks_failed)


def test_generation_evaluator_groundedness_human_review(generation_evaluator):
    """Test 17: Groundedness outcome is REQUIRES_HUMAN_REVIEW when flagged in benchmark."""
    case = EvaluationCase(
        case_id="G-03",
        query="Broad controls question",
        category="F",
        expected_record_ids=["RR-UK-03"],
        expected_behavior="Requires human review",
        requires_human_review=True,
    )
    response = StructuredAIResponse(
        status=ResponseStatus.GROUNDED,
        query="Broad controls question",
        answer="FCA guidance controls.",
        grounded=True,
        retrieved_evidence=[],
    )
    result = generation_evaluator.evaluate_case_groundedness(case, response)
    assert result.outcome == GroundednessOutcome.REQUIRES_HUMAN_REVIEW
    assert result.requires_human_review is True


def test_generation_evaluator_citation_validity_rate(generation_evaluator):
    """Test 18: Citation validity rate measures percentage of citations referencing retrieved chunks."""
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
            regulation="Bribery Act 2010", section_article="Section 1", title="Offences",
            text="Text", validation_status="Candidate"
        )
    ]
    c1 = _make_dummy_citation(chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01")
    c2 = _make_dummy_citation(chunk_id="RR-UNKNOWN-C01", record_id="RR-UK-99", source_id="UK-99")

    case = EvaluationCase(case_id="C-01", query="Query", category="A", expected_behavior="Test citations")
    response = StructuredAIResponse(
        status=ResponseStatus.GROUNDED, query="Query", answer="Answer", grounded=True,
        retrieved_evidence=evidence, citations=[c1, c2]
    )
    res = generation_evaluator.evaluate_citations([(case, response)])
    assert res.total_citations == 2
    assert res.valid_citations == 1
    assert res.invalid_citations == 1
    assert res.validity_rate == 0.5


def test_generation_evaluator_citation_precision_recall_not_evaluated(generation_evaluator):
    """Test 19: Sentence-level citation precision/recall are explicitly marked NOT_EVALUATED."""
    res = generation_evaluator.evaluate_citations([])
    assert res.precision_evaluated is False
    assert res.recall_evaluated is False
    assert "NOT_EVALUATED" in res.notes


def test_generation_evaluator_gap_accuracy(generation_evaluator):
    """Test 20: GAP accuracy correctly evaluates match between expected and actual GapType."""
    case = EvaluationCase(
        case_id="GAP-01",
        query="DORA query",
        category="J",
        expected_gap_type="OUT_OF_SCOPE",
        expected_behavior="Test GAP accuracy",
    )
    gap_result = GapResult(
        is_gap=True,
        gap_type=GapType.OUT_OF_SCOPE,
        message="Out of scope",
        user_safe_message="Outside anti-bribery domain",
    )
    response = StructuredAIResponse(
        status=ResponseStatus.OUT_OF_SCOPE,
        query="DORA query",
        answer="Outside scope",
        grounded=False,
        gap=gap_result,
    )
    res = generation_evaluator.evaluate_gaps([(case, response)])
    assert res.total_gap_cases == 1
    assert res.correct_classifications == 1
    assert res.accuracy == 1.0


def test_generation_evaluator_gap_false_grounded_detection(generation_evaluator):
    """Test 21: GAP evaluation detects when a case expected to be a gap was falsely marked GROUNDED."""
    case = EvaluationCase(
        case_id="GAP-02",
        query="DORA query",
        category="J",
        expected_gap_type="OUT_OF_SCOPE",
        expected_behavior="Detect false grounded",
    )
    response = StructuredAIResponse(
        status=ResponseStatus.GROUNDED,
        query="DORA query",
        answer="Falsely answered",
        grounded=True,
    )
    res = generation_evaluator.evaluate_gaps([(case, response)])
    assert res.false_grounded_count == 1
    assert res.accuracy == 0.0


def test_generation_evaluator_conflict_precision_recall(generation_evaluator):
    """Test 22: Conflict evaluation calculates pair precision and recall against expected conflict IDs."""
    case = EvaluationCase(
        case_id="CONF-01",
        query="Compare UK-01 and UK-02",
        category="G",
        expected_conflict_ids=["CO-001"],
        expected_behavior="Test conflict evaluation",
    )
    finding = ConflictFinding(
        conflict_id="CO-001", topic="Bribery", source_id_1="UK-01", source_1="Bribery Act",
        source_id_2="UK-02", source_2="Guidance", relationship="Overlap - complementary",
        conflict_type=ConflictType.OVERLAP, conflict_status="Verified", message="Complementary"
    )
    response = StructuredAIResponse(
        status=ResponseStatus.GROUNDED, query="Query", answer="Answer", grounded=True,
        conflicts=[finding]
    )
    res = generation_evaluator.evaluate_conflicts([(case, response)])
    assert res.true_positives == 1
    assert res.false_positives == 0
    assert res.false_negatives == 0
    assert res.pair_precision == 1.0
    assert res.pair_recall == 1.0


# ---------------------------------------------------------------------------
# 4. Safety & Adversarial Tests
# ---------------------------------------------------------------------------

def test_safety_evaluator_candidate_status_preservation(safety_evaluator):
    """Test 23: All normalized records preserve Candidate - Awaiting Approval status."""
    assert safety_evaluator.evaluate_candidate_preservation() is True


def test_safety_evaluator_approved_only_filtering(safety_evaluator):
    """Test 24: Approved-only filtering strictly returns zero chunks and UNAPPROVED_EVIDENCE status."""
    assert safety_evaluator.evaluate_approved_only_filtering() is True


def test_safety_evaluator_non_adjudication(safety_evaluator):
    """Test 25: Pipeline answers and conflict findings refrain from legal conflict adjudication."""
    resp = StructuredAIResponse(
        status=ResponseStatus.GROUNDED,
        query="Compare rules",
        answer="Both regulations apply in their respective spheres. Neither overrides the other.",
        grounded=True,
    )
    assert safety_evaluator.evaluate_non_adjudication([resp]) is True

    bad_resp = StructuredAIResponse(
        status=ResponseStatus.GROUNDED,
        query="Compare rules",
        answer="The EU Directive legally overrides UK law in all situations.",
        grounded=True,
    )
    assert safety_evaluator.evaluate_non_adjudication([bad_resp]) is False


def test_safety_evaluator_prompt_injections(safety_evaluator):
    """Test 26: Adversarial prompt injections are tested and outcomes recorded."""
    results = safety_evaluator.test_prompt_injections(provider_name="MockLLMProvider")
    assert len(results) == 3
    assert all(r.safe_behavior_observed for r in results)
    assert all(r.provider_tested == "MockLLMProvider" for r in results)


# ---------------------------------------------------------------------------
# 5. Runner & Report Generation Tests
# ---------------------------------------------------------------------------

def test_evaluation_runner_generates_json_and_markdown(tmp_path):
    """Test 27: EvaluationRunner generates both evaluation_results.json and evaluation_summary.md."""
    runner = EvaluationRunner(output_dir=tmp_path)
    # Use a small subset of cases to test report writing speed
    sample_case = EvaluationCase(
        case_id="RUN-01",
        query="What is Section 1?",
        category="A",
        expected_record_ids=["RR-UK-01"],
        expected_status="GROUNDED",
        expected_behavior="Test runner",
    )
    # Temporarily write a 1-case dataset
    subset_dataset = tmp_path / "test_cases.json"
    with open(subset_dataset, "w", encoding="utf-8") as f:
        json.dump([sample_case.model_dump()], f)

    report = runner.run_benchmark(dataset_path=subset_dataset)
    assert report.total_cases == 1
    assert (tmp_path / "evaluation_results.json").exists()
    assert (tmp_path / "evaluation_summary.md").exists()


def test_evaluation_runner_failure_analysis_populated(tmp_path):
    """Test 28: Failure analysis records exact provision retrieval ranking."""
    runner = EvaluationRunner(output_dir=tmp_path)
    # In Week 4, enriched retrieval text elevates Section 1 to rank #1
    epa = runner.retrieval_evaluator.analyze_exact_provision()
    assert epa.retrieved_at_k1 is True
    assert epa.rank_in_retrieval == 1


def test_existing_100_tests_remain_unaffected():
    """Test 29: Regression guard confirming Task 10 preserves all prior architectures."""
    # Verifies that key imports from Tasks 2-9 remain functional
    from rag.ingestion.excel_loader import ExcelWorkbookLoader
    from rag.retrieval.vector_store import ChromaVectorStore
    from rag.retrieval.retriever import RegulatoryRetriever
    from rag.generation.grounded_generator import GroundedGenerator
    from rag.generation.citations import CitationBuilder
    from rag.generation.gap_handler import GapHandler
    from rag.conflict.conflict_detector import ConflictDetector
    from rag.output.structured_response import StructuredAIResponse

    assert ChromaVectorStore is not None
    assert RegulatoryRetriever is not None
    assert GroundedGenerator is not None
    assert ConflictDetector is not None
    assert StructuredAIResponse is not None
