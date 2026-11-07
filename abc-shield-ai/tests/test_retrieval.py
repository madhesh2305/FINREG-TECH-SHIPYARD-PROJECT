"""Test suite for Vector Retrieval (Task 4).

Verifies semantic retrieval over ChromaDB:
- Query embedding generation
- Result retrieval and top_k parameter compliance
- Preservation of chunk_id, record_id, source_id, and full provenance metadata
- Distance and similarity score calculation
- Jurisdiction filtering ("UK", "EU")
- Approved-only filtering guardrail (must return 0 for candidate dataset)
- Reopening and reusing existing persistent ChromaDB
- Evidence-only output (strictly zero LLM answer generation)
- Semantic relevance differentiation across test queries
"""

from pathlib import Path
import json
import pytest

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult


CHUNKS_PATH = Path("data/processed/regulatory_chunks.json")
EXISTING_CHROMA_DIR = Path("data/processed/chroma_db")


@pytest.fixture(scope="module")
def loaded_chunks():
    """Load pre-processed regulatory chunks from Task 2."""
    assert CHUNKS_PATH.exists(), f"Processed chunks file missing at {CHUNKS_PATH}"
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [RegulatoryChunk(**c) for c in data]


@pytest.fixture(scope="module")
def embedding_manager():
    """Shared EmbeddingManager instance using all-MiniLM-L6-v2."""
    return EmbeddingManager(model_name="all-MiniLM-L6-v2")


@pytest.fixture(scope="module")
def chunk_embeddings(embedding_manager, loaded_chunks):
    """Pre-computed embeddings for loaded chunks."""
    texts = [c.text for c in loaded_chunks]
    return embedding_manager.embed_texts(texts)


@pytest.fixture(scope="module")
def persistent_retriever(embedding_manager):
    """Retriever connected to the existing persistent ChromaDB."""
    store = ChromaVectorStore(persist_dir=EXISTING_CHROMA_DIR, collection_name="regulatory_records")
    return RegulatoryRetriever(embedding_manager=embedding_manager, vector_store=store)


# 1. Query embedding generation works
def test_1_query_embedding_works(embedding_manager):
    query = "What does the Bribery Act 2010 say about bribing another person?"
    emb = embedding_manager.embed_text(query)
    assert isinstance(emb, list)
    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)


# 2. Retrieval returns results from ChromaDB
def test_2_retrieval_returns_results(persistent_retriever):
    results = persistent_retriever.retrieve("anti-bribery controls", top_k=3)
    assert len(results) > 0
    assert all(isinstance(r, RetrievalResult) for r in results)


# 3. top_k is respected
def test_3_top_k_is_respected(persistent_retriever):
    results_1 = persistent_retriever.retrieve("anti-bribery", top_k=1)
    results_3 = persistent_retriever.retrieve("anti-bribery", top_k=3)
    results_5 = persistent_retriever.retrieve("anti-bribery", top_k=5)

    assert len(results_1) == 1
    assert len(results_3) == 3
    assert len(results_5) == 5


# 4. Chunk IDs are preserved
def test_4_chunk_ids_are_preserved(persistent_retriever):
    results = persistent_retriever.retrieve("bribery", top_k=5)
    for res in results:
        assert res.chunk_id.startswith("RR-")
        assert "-C" in res.chunk_id


# 5. Source IDs are preserved
def test_5_source_ids_are_preserved(persistent_retriever):
    results = persistent_retriever.retrieve("bribery", top_k=5)
    for res in results:
        assert res.source_id.startswith("UK-") or res.source_id.startswith("EU-")


# 6. Record IDs are preserved
def test_6_record_ids_are_preserved(persistent_retriever):
    results = persistent_retriever.retrieve("bribery", top_k=5)
    for res in results:
        assert res.record_id.startswith("RR-")


# 7. Metadata is preserved across retrieval
def test_7_metadata_is_preserved(persistent_retriever):
    results = persistent_retriever.retrieve("Bribery Act 2010 offences", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert top.regulation != ""
    assert top.regulator != ""
    assert top.jurisdiction in ("UK", "EU")
    assert top.section_article != ""
    assert top.title != ""
    assert top.text != ""
    assert top.text_type in ("requirement_paraphrase", "retrieval_text")
    assert top.validation_status == "Candidate - Awaiting Approval"
    assert top.is_approved_for_rag is False


# 8. Distance and similarity score are returned
def test_8_distance_and_similarity_returned(persistent_retriever):
    results = persistent_retriever.retrieve("What are practical anti-bribery controls?", top_k=3)
    assert len(results) > 0
    for res in results:
        assert 0.0 <= res.similarity_score <= 1.0
        assert res.distance >= 0.0
        # Cosine distance and similarity relation
        assert abs(res.similarity_score - round(1.0 - res.distance, 4)) < 0.001


# 9. Jurisdiction filtering works
def test_9_jurisdiction_filtering_works(persistent_retriever):
    uk_results = persistent_retriever.retrieve("anti-corruption", top_k=5, jurisdiction="UK")
    assert len(uk_results) > 0
    assert all(r.jurisdiction == "UK" for r in uk_results)

    eu_results = persistent_retriever.retrieve("anti-corruption", top_k=5, jurisdiction="EU")
    assert len(eu_results) > 0
    assert all(r.jurisdiction == "EU" for r in eu_results)


# 10. Approved-only filtering works and returns zero for current candidate dataset
def test_10_approved_only_filter_returns_zero_for_candidate_dataset(persistent_retriever):
    # With filter_approved_only=True, no candidate records must ever be returned
    results = persistent_retriever.retrieve("Bribery Act 2010", top_k=5, filter_approved_only=True)
    assert len(results) == 0, "Approved-only filter must return 0 records because all current records are Candidate."


# 11. ChromaDB persistence is reused after reopening
def test_11_chromadb_persistence_reused_after_reopening(embedding_manager):
    # Instantiate a new ChromaVectorStore on the existing directory without modifying data
    store = ChromaVectorStore(persist_dir=EXISTING_CHROMA_DIR, collection_name="regulatory_records")
    stats = store.get_collection_stats()
    assert stats["total_vectors"] == 15
    assert stats["collection_name"] == "regulatory_records"

    retriever = RegulatoryRetriever(embedding_manager=embedding_manager, vector_store=store)
    res = retriever.retrieve("integrity", top_k=1)
    assert len(res) == 1
    assert res[0].chunk_id != ""


# 12. No LLM generation occurs during retrieval (evidence only)
def test_12_no_llm_generation_occurs_during_retrieval(persistent_retriever):
    results = persistent_retriever.retrieve("What does the Bribery Act 2010 say about bribing another person?", top_k=3)
    for res in results:
        # Verify that output is purely structured evidence without AI-generated conclusions
        dumped = res.model_dump()
        assert "generated_answer" not in dumped
        assert "llm_response" not in dumped
        assert "legal_conclusion" not in dumped
        # Text must strictly match the ingested requirement paraphrase or retrieval text
        assert res.text_type in ("requirement_paraphrase", "retrieval_text")
        assert res.validation_status == "Candidate - Awaiting Approval"


# 13. Test Query 1: What does the Bribery Act 2010 say about bribing another person?
def test_13_query_1_bribery_act(persistent_retriever):
    query = "What does the Bribery Act 2010 say about bribing another person?"
    results = persistent_retriever.retrieve(query, top_k=5)
    assert len(results) == 5
    chunk_ids = [r.chunk_id for r in results]
    assert "RR-UK-01-C01" in chunk_ids or "RR-UK-07-C01" in chunk_ids
    assert results[0].jurisdiction == "UK"
    for r in results:
        assert r.jurisdiction in ("UK", "EU")
        assert r.validation_status == "Candidate - Awaiting Approval"
        assert r.is_approved_for_rag is False


# 14. Test Query 2: What are practical anti-bribery controls?
def test_14_query_2_practical_controls(persistent_retriever):
    query = "What are practical anti-bribery controls?"
    results = persistent_retriever.retrieve(query, top_k=3)
    assert len(results) == 3
    # Top result should be the practical anti-bribery controls note (RR-UK-07-C01)
    assert results[0].chunk_id == "RR-UK-07-C01"
    assert results[0].similarity_score > 0.60
    assert results[0].validation_status == "Candidate - Awaiting Approval"


# 15. Test Query 3: What cybersecurity requirements apply? (Out-of-scope relevance test)
def test_15_query_3_cybersecurity_out_of_scope(persistent_retriever):
    query = "What cybersecurity requirements apply?"
    results = persistent_retriever.retrieve(query, top_k=3)
    assert len(results) == 3
    # Because cybersecurity is outside the anti-bribery scope, similarity scores should be low (< 0.35)
    for r in results:
        assert r.similarity_score < 0.35
        assert r.distance > 0.65
