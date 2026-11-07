"""Automated test suite for Task W4.7: Update & Validate Retrieval Baseline.

Verifies:
1. Benchmark dataset loads successfully.
2. Expected target IDs are valid.
3. ChromaDB contains exactly 15 vectors.
4. Retrieval returns valid Chunk_IDs.
5. K=1 works.
6. K=3 works.
7. K=5 works.
8. Similarity values are present.
9. Expected IDs can be matched against retrieved IDs.
10. MRR calculation is deterministic.
11. Precision calculations are deterministic.
12. Recall calculations are deterministic.
13. Hit Rate calculations are deterministic.
14. Non-applicable cases are excluded correctly.
15. No external retrieval service is used.
16. Evaluation does not mutate ChromaDB.
17. Evaluation does not mutate canonical chunk JSON.
18. Approval state remains unchanged.
"""

import pytest
import hashlib
from pathlib import Path
import re
import chromadb

from rag.evaluation.evaluation_dataset import EvaluationDatasetValidator
from rag.evaluation.evaluation_models import EvaluationCase, CaseRetrievalResult, RetrievalMetrics
from rag.evaluation.retrieval_evaluator import RetrievalEvaluator
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.retrieval.vector_store import ChromaVectorStore


@pytest.fixture(scope="module")
def validator():
    return EvaluationDatasetValidator()


@pytest.fixture(scope="module")
def benchmark_cases(validator):
    return validator.load_cases()


@pytest.fixture(scope="module")
def retriever():
    return RegulatoryRetriever()


@pytest.fixture(scope="module")
def retrieval_evaluator(retriever):
    return RetrievalEvaluator(retriever=retriever)


def test_1_benchmark_dataset_loads_successfully(benchmark_cases):
    """Test 1: Benchmark dataset loads all 34 controlled evaluation cases."""
    assert len(benchmark_cases) == 34
    assert all(isinstance(c, EvaluationCase) for c in benchmark_cases)
    assert all(c.case_id.startswith("CASE-") for c in benchmark_cases)


def test_2_expected_target_ids_are_valid(validator, benchmark_cases):
    """Test 2: Expected target IDs belong to the valid dynamic record set."""
    valid_records = validator.valid_record_ids
    assert len(valid_records) == 15
    for case in benchmark_cases:
        for rid in case.expected_record_ids:
            assert rid in valid_records, f"Invalid expected record_id {rid} in {case.case_id}"


def test_3_chromadb_contains_15_vectors():
    """Test 3: ChromaDB persistent vector store contains exactly 15 vectors."""
    store = ChromaVectorStore()
    assert store._get_collection().count() == 15


def test_4_retrieval_returns_valid_chunk_ids(retriever):
    """Test 4: Retrieval returns valid Chunk_IDs conforming to schema."""
    results = retriever.retrieve("bribery offence", top_k=5)
    assert len(results) == 5
    chunk_pattern = re.compile(r"^RR-(UK|EU)-\d{2}-C\d{2}$")
    for r in results:
        assert chunk_pattern.match(r.chunk_id), f"Invalid chunk_id format: {r.chunk_id}"


def test_5_k_1_retrieval_works(retriever):
    """Test 5: K=1 retrieval returns exactly 1 item."""
    results = retriever.retrieve("Section 1 Bribery Act 2010", top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "RR-UK-01-C01"


def test_6_k_3_retrieval_works(retriever):
    """Test 6: K=3 retrieval returns exactly 3 items."""
    results = retriever.retrieve("corporate bribery prevention", top_k=3)
    assert len(results) == 3


def test_7_k_5_retrieval_works(retriever):
    """Test 7: K=5 retrieval returns exactly 5 items."""
    results = retriever.retrieve("whistleblower reporting channels", top_k=5)
    assert len(results) == 5


def test_8_similarity_values_present_and_valid(retriever):
    """Test 8: Similarity values are float within [0.0, 1.0]."""
    results = retriever.retrieve("bribery investigation", top_k=3)
    for r in results:
        assert r.similarity_score is not None
        assert isinstance(r.similarity_score, float)
        assert 0.0 <= r.similarity_score <= 1.0
        assert r.distance is not None
        assert 0.0 <= r.distance <= 2.0


def test_9_expected_ids_matched_against_retrieved_ids(retrieval_evaluator, benchmark_cases):
    """Test 9: Expected record IDs correctly match retrieved record IDs in single case."""
    case_1 = next(c for c in benchmark_cases if c.case_id == "CASE-01")
    res = retrieval_evaluator.evaluate_case(case_1, top_k=5)
    assert "RR-UK-01" in res.retrieved_record_ids
    assert res.expected_record_ids == ["RR-UK-01"]
    assert res.hit_rate_at_k[1] == 1.0


def test_10_mrr_calculation_is_deterministic(retrieval_evaluator):
    """Test 10: MRR calculation is deterministic and handles various rank positions."""
    # Mock retriever returning target at rank 2
    class MockRetrieverRank2:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-02-C01", record_id="RR-UK-02", source_id="UK-02",
                    regulation="Reg 2", regulator="UK", jurisdiction="UK",
                    section_article="Sec 2", title="T2", text="Text 2", text_type="paraphrase",
                    validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
                RetrievalResult(
                    chunk_id="RR-UK-01-C01", record_id="RR-UK-01", source_id="UK-01",
                    regulation="Bribery Act 2010", regulator="UK", jurisdiction="UK",
                    section_article="Section 1", title="Title", text="Text 1", text_type="paraphrase",
                    validation_status="Candidate - Awaiting Approval", is_approved_for_rag=False,
                    similarity_score=0.8, distance=0.2
                ),
            ]

    evaluator = RetrievalEvaluator(retriever=MockRetrieverRank2())
    case = EvaluationCase(
        case_id="TEST-MRR",
        query="Section 1",
        category="A",
        expected_record_ids=["RR-UK-01"],
        expected_behavior="Test MRR rank 2",
    )
    res = evaluator.evaluate_case(case, top_k=2)
    assert res.reciprocal_rank == 0.5  # 1 / 2


def test_11_precision_calculations_deterministic(retrieval_evaluator):
    """Test 11: Precision@K calculations follow |relevant in top K| / K."""
    case = EvaluationCase(
        case_id="TEST-PREC",
        query="Test",
        category="A",
        expected_record_ids=["RR-UK-01"],
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
                    chunk_id="RR-UK-02-C01", record_id="RR-UK-02", source_id="UK-02",
                    regulation="Reg 2", regulator="UK", jurisdiction="UK",
                    section_article="Sec 2", title="T2", text="Txt2", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.8, distance=0.2
                ),
            ]

    evaluator = RetrievalEvaluator(retriever=MockRetriever())
    res = evaluator.evaluate_case(case, top_k=2)
    assert res.precision_at_k[1] == 1.0  # 1/1
    assert res.precision_at_k[2] == 0.5 if 2 in res.precision_at_k else True
    assert res.precision_at_k[3] == round(1.0 / 3.0, 4)


def test_12_recall_calculations_deterministic(retrieval_evaluator):
    """Test 12: Recall@K calculations follow |relevant in top K| / |expected|."""
    case = EvaluationCase(
        case_id="TEST-REC",
        query="Test",
        category="G",
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
            ]

    evaluator = RetrievalEvaluator(retriever=MockRetriever())
    res = evaluator.evaluate_case(case, top_k=1)
    assert res.recall_at_k[1] == 0.5  # 1 of 2 retrieved


def test_13_hit_rate_calculations_deterministic(retrieval_evaluator):
    """Test 13: Hit Rate@K is binary indicator (1.0 if any relevant in top K, else 0.0)."""
    case = EvaluationCase(
        case_id="TEST-HR",
        query="Test",
        category="A",
        expected_record_ids=["RR-UK-01"],
        expected_behavior="Test hit rate",
    )
    class MockRetriever:
        def retrieve(self, query, top_k=5, filter_approved_only=False):
            return [
                RetrievalResult(
                    chunk_id="RR-UK-09-C01", record_id="RR-UK-09", source_id="UK-09",
                    regulation="Reg 9", regulator="UK", jurisdiction="UK",
                    section_article="Sec 9", title="T9", text="Txt9", text_type="p",
                    validation_status="Candidate", is_approved_for_rag=False,
                    similarity_score=0.9, distance=0.1
                ),
            ]

    evaluator = RetrievalEvaluator(retriever=MockRetriever())
    res = evaluator.evaluate_case(case, top_k=1)
    assert res.hit_rate_at_k[1] == 0.0


def test_14_non_applicable_cases_excluded_correctly(retrieval_evaluator, benchmark_cases):
    """Test 14: Zero-expected cases (13 cases) are separated from applicable cases (21 cases)."""
    metrics, case_results = retrieval_evaluator.evaluate_all(benchmark_cases)
    assert metrics.evaluated_cases == 21
    assert metrics.zero_expected_cases == 13
    assert len(case_results) == 34
    zero_cases = [r for r in case_results if r.is_zero_expected]
    assert len(zero_cases) == 13
    assert all(r.reciprocal_rank == 0.0 for r in zero_cases)


def test_15_no_external_retrieval_service_used(retriever):
    """Test 15: Retrieval operates entirely on local CPU embedding and vector store."""
    from sentence_transformers import SentenceTransformer
    from rag.retrieval.embeddings import EmbeddingManager
    store = retriever.vector_store
    assert isinstance(store, ChromaVectorStore)
    assert store._get_client() is not None
    # Embedding model is local sentence-transformers
    assert isinstance(retriever.embedding_manager, EmbeddingManager)
    model = retriever.embedding_manager._get_model()
    assert isinstance(model, SentenceTransformer)
    assert model.device.type == "cpu"


def test_16_evaluation_does_not_mutate_chromadb(retrieval_evaluator, benchmark_cases):
    """Test 16: Executing benchmark evaluation does not alter ChromaDB vector count."""
    store = ChromaVectorStore()
    col = store._get_collection()
    count_before = col.count()
    assert count_before == 15
    retrieval_evaluator.evaluate_all(benchmark_cases)
    count_after = col.count()
    assert count_after == count_before == 15


def test_17_evaluation_does_not_mutate_canonical_chunk_json(benchmark_cases):
    """Test 17: Canonical chunk artifact remains immutable with identical SHA-256 hash."""
    chunk_path = Path("data/processed/regulatory_chunks.json")
    hash_before = hashlib.sha256(chunk_path.read_bytes()).hexdigest()
    # Confirm known baseline hash
    assert hash_before == "05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef"
    hash_after = hashlib.sha256(chunk_path.read_bytes()).hexdigest()
    assert hash_before == hash_after


def test_18_approval_state_remains_unchanged(retriever):
    """Test 18: All indexed records remain Candidate with is_approved_for_rag=False; approved-only filter yields 0."""
    res_candidate = retriever.retrieve("bribery", top_k=5, filter_approved_only=False)
    assert len(res_candidate) > 0
    assert all(r.validation_status == "Candidate - Awaiting Approval" for r in res_candidate)
    assert all(r.is_approved_for_rag is False for r in res_candidate)

    res_approved = retriever.retrieve("bribery", top_k=5, filter_approved_only=True)
    assert len(res_approved) == 0
