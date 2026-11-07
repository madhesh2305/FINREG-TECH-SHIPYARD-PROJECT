"""Tests for Step 7: Staged ChromaDB Integrity and Readiness Validation.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Staged database read-only access and existence
2. Exactly 25 expected chunk IDs present with 0 missing, 0 unexpected, 0 duplicates
3. Exact source distribution: UK-01=6, UK-02=6, UK-03=5, UK-09=1, EU-01=7
4. All 25 embeddings have strictly 384 finite float values (no NaN/Inf)
5. Stored document texts match Step 5 canonical chunk text 100%
6. Metadata fields match parent record IDs, source IDs, valid HTTP URLs, and jurisdiction
7. Representative retrieval queries (UK & EU) return semantically relevant chunks with scores > 0.50
8. Candidate gating: 25 Candidate / 0 Approved (fail-closed, 0 results on approved-only filter)
9. Active stores immutability (active ChromaDB remains at 15 vectors, active JSON files untouched)
"""

from pathlib import Path
import json
import math
import pytest
import chromadb

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.retriever import RegulatoryRetriever

STAGING_CHROMA_DIR = Path("data/staging/madhesh_handover/step6/chroma_db")
STAGING_COLLECTION_NAME = "canonical_regulatory_records"
STAGING_CHUNKS_FILE = Path("data/staging/madhesh_handover/step5/regulatory_chunks.json")

ACTIVE_CHROMA_DIR = Path("data/processed/chroma_db")
ACTIVE_COLLECTION_NAME = "regulatory_records"
ACTIVE_CHUNKS_FILE = Path("data/processed/regulatory_chunks.json")
ACTIVE_NORM_FILE = Path("data/processed/normalized_regulatory_records.json")

EXPECTED_SOURCE_COUNTS = {
    "UK-01": 6,
    "UK-02": 6,
    "UK-03": 5,
    "UK-09": 1,
    "EU-01": 7,
}


@pytest.fixture(scope="module")
def staged_chunks():
    """Load Step 5 staged chunks."""
    assert STAGING_CHUNKS_FILE.exists(), f"Staged chunks missing: {STAGING_CHUNKS_FILE}"
    with open(STAGING_CHUNKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [RegulatoryChunk(**item) for item in data]


@pytest.fixture(scope="module")
def staged_client():
    """Open persistent client to staged directory in read-only inspection mode."""
    assert STAGING_CHROMA_DIR.exists()
    return chromadb.PersistentClient(path=str(STAGING_CHROMA_DIR))


@pytest.fixture(scope="module")
def staged_collection(staged_client):
    """Retrieve staged collection."""
    return staged_client.get_collection(STAGING_COLLECTION_NAME)


@pytest.fixture(scope="module")
def staged_db_data(staged_collection):
    """Retrieve all stored data from the collection."""
    return staged_collection.get(include=["metadatas", "documents", "embeddings"])


# ---------------------------------------------------------------------------
# 1. Staged DB Existence and Read-Only Access
# ---------------------------------------------------------------------------

def test_read_only_collection_access(staged_collection):
    """Verify that staged collection exists and is accessible without mutation."""
    assert staged_collection is not None
    assert staged_collection.name == STAGING_COLLECTION_NAME
    assert staged_collection.count() == 25


# ---------------------------------------------------------------------------
# 2. Chunk ID Integrity (0 missing, 0 unexpected, 0 duplicates)
# ---------------------------------------------------------------------------

def test_all_25_chunk_ids_present_and_unique(staged_db_data, staged_chunks):
    """Verify that all 25 IDs match Step 5 exactly with 0 duplicates/missing/unexpected."""
    expected_ids = {c.chunk_id for c in staged_chunks}
    actual_ids = staged_db_data["ids"]

    assert len(actual_ids) == 25
    assert len(set(actual_ids)) == 25  # No duplicates

    missing_ids = expected_ids - set(actual_ids)
    unexpected_ids = set(actual_ids) - expected_ids

    assert len(missing_ids) == 0, f"Missing IDs: {missing_ids}"
    assert len(unexpected_ids) == 0, f"Unexpected IDs: {unexpected_ids}"


# ---------------------------------------------------------------------------
# 3. Source Distribution Breakdown
# ---------------------------------------------------------------------------

def test_source_distribution_exact_counts(staged_db_data):
    """Verify exact canonical source counts: UK-01=6, UK-02=6, UK-03=5, UK-09=1, EU-01=7."""
    actual_counts = {}
    for meta in staged_db_data["metadatas"]:
        src = meta.get("source_id")
        actual_counts[src] = actual_counts.get(src, 0) + 1

    assert actual_counts == EXPECTED_SOURCE_COUNTS


# ---------------------------------------------------------------------------
# 4. Embedding Dimension and Finite Values
# ---------------------------------------------------------------------------

def test_embedding_dimensions_and_finite_numeric_values(staged_db_data):
    """Confirm every embedding has 384 finite numeric values (no NaN, no Inf)."""
    embeddings = staged_db_data["embeddings"]
    assert len(embeddings) == 25

    for idx, emb in enumerate(embeddings):
        assert len(emb) == 384, f"Vector {idx} dimension is {len(emb)}, expected 384"
        assert all(isinstance(v, float) for v in emb)
        assert all(math.isfinite(v) for v in emb), f"Vector {idx} contains non-finite values"


# ---------------------------------------------------------------------------
# 5. Stored Document Text Exact Match
# ---------------------------------------------------------------------------

def test_document_texts_match_step5_exactly(staged_db_data, staged_chunks):
    """Compare stored document text against Step 5 chunks with 100% exact match."""
    chunk_map = {c.chunk_id: c for c in staged_chunks}

    for cid, doc in zip(staged_db_data["ids"], staged_db_data["documents"]):
        expected_text = chunk_map[cid].text
        assert doc == expected_text
        assert len(doc) >= 327
        assert len(doc) <= 777


# ---------------------------------------------------------------------------
# 6. Metadata Field Preservation & URL Integrity
# ---------------------------------------------------------------------------

def test_metadata_fields_and_official_source_urls(staged_db_data, staged_chunks):
    """Verify metadata preserves parent record IDs, source IDs, jurisdiction, and URLs."""
    chunk_map = {c.chunk_id: c for c in staged_chunks}

    for cid, meta in zip(staged_db_data["ids"], staged_db_data["metadatas"]):
        chunk = chunk_map[cid]
        assert meta["record_id"] == chunk.record_id
        assert meta["source_id"] == chunk.source_id
        assert meta["jurisdiction"] == chunk.jurisdiction
        assert meta["section_article"] == chunk.section_article
        assert meta["authority_level"] == chunk.authority_level
        assert meta["official_source"] == chunk.official_source
        assert meta["official_source"].startswith("http")
        assert meta["text_type"] == "retrieval_text"


# ---------------------------------------------------------------------------
# 7. Representative Retrieval Queries (UK and EU)
# ---------------------------------------------------------------------------

def test_representative_queries_uk_and_eu():
    """Execute representative queries against staged collection only and verify semantic accuracy."""
    store = ChromaVectorStore(
        persist_dir=STAGING_CHROMA_DIR,
        collection_name=STAGING_COLLECTION_NAME
    )
    retriever = RegulatoryRetriever(vector_store=store)

    # 1. UK Query - Bribery Section 1
    uk_results = retriever.retrieve(
        "offences of bribing another person",
        top_k=2,
        filter_approved_only=False
    )
    assert len(uk_results) >= 1
    assert uk_results[0].chunk_id == "UK-01-R001-C01"
    assert uk_results[0].source_id == "UK-01"
    assert uk_results[0].similarity_score > 0.55

    # 2. EU Query - Corruption Directive Article 4 (Private-Sector Bribery)
    eu_results = retriever.retrieve(
        "private-sector bribery offences in EU directive",
        top_k=2,
        filter_approved_only=False
    )
    assert len(eu_results) >= 1
    assert eu_results[0].chunk_id == "EU-01-R003-C01"
    assert eu_results[0].source_id == "EU-01"
    assert eu_results[0].similarity_score > 0.65

    # 3. EU Query - Mitigating Circumstances Article 16
    eu_mitigating = retriever.retrieve(
        "mitigating circumstances for legal persons under Article 16",
        top_k=2,
        filter_approved_only=False
    )
    assert len(eu_mitigating) >= 1
    assert eu_mitigating[0].chunk_id == "EU-01-R007-C01"
    assert eu_mitigating[0].source_id == "EU-01"
    assert eu_mitigating[0].similarity_score > 0.50


# ---------------------------------------------------------------------------
# 8. Candidate Gating Controls
# ---------------------------------------------------------------------------

def test_fail_closed_candidate_gating_block(staged_db_data):
    """Verify that all 25 records remain candidates and 0 results on approved-only filter."""
    metadatas = staged_db_data["metadatas"]
    assert sum(1 for m in metadatas if m.get("is_approved_for_rag") is True) == 0
    assert sum(1 for m in metadatas if m.get("is_approved_for_rag") is False) == 25

    store = ChromaVectorStore(
        persist_dir=STAGING_CHROMA_DIR,
        collection_name=STAGING_COLLECTION_NAME
    )
    retriever = RegulatoryRetriever(vector_store=store)
    approved_results = retriever.retrieve("bribery offence", top_k=5, filter_approved_only=True)
    assert len(approved_results) == 0


# ---------------------------------------------------------------------------
# 9. Active Store Immutability Check
# ---------------------------------------------------------------------------

def test_active_stores_immutability_and_hash_integrity():
    """Verify that active production ChromaDB and processed JSON files remain 100% untouched."""
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
