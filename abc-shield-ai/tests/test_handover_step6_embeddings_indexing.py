"""Tests for Step 6: Canonical Embeddings and Staged ChromaDB Indexing.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Staged ChromaDB directory and sqlite database exist
2. Exactly 25 vectors in collection 'canonical_regulatory_records'
3. Deterministic and unique Chunk_IDs matching canonical 25 corpus
4. Embedding dimension strictly 384 and all values finite floats (no NaN/Inf)
5. Stored ChromaDB documents exactly match Step 5 canonical chunk text
6. Full metadata preservation (Record_ID, Source_ID, URL, Jurisdiction, Section/Article, Topic)
7. Candidate gating: 25 Candidate / 0 Approved (is_approved_for_rag = False)
8. Fresh PersistentClient reload from disk
9. Staged retrieval smoke test with similarity scoring
10. Active stores immutability (data/processed/chroma_db has 15 vectors, processed JSON files have 15 items)
"""

from pathlib import Path
import json
import math
import pytest
import chromadb

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.retriever import RegulatoryRetriever

STAGING_CHROMA_DIR = Path("data/staging/madhesh_handover/step6/chroma_db")
STAGING_COLLECTION_NAME = "canonical_regulatory_records"
STAGING_CHUNKS_FILE = Path("data/staging/madhesh_handover/step5/regulatory_chunks.json")

ACTIVE_CHROMA_DIR = Path("data/processed/chroma_db")
ACTIVE_COLLECTION_NAME = "regulatory_records"
ACTIVE_CHUNKS_FILE = Path("data/processed/regulatory_chunks.json")
ACTIVE_NORM_FILE = Path("data/processed/normalized_regulatory_records.json")

EXPECTED_CANONICAL_25_IDS = [
    "UK-01-R001-C01", "UK-01-R002-C01", "UK-01-R003-C01", "UK-01-R004-C01", "UK-01-R005-C01", "UK-01-R006-C01",
    "UK-02-R001-C01", "UK-02-R002-C01", "UK-02-R003-C01", "UK-02-R004-C01", "UK-02-R005-C01", "UK-02-R006-C01",
    "UK-03-R001-C01", "UK-03-R002-C01", "UK-03-R003-C01", "UK-03-R004-C01", "UK-03-R005-C01",
    "UK-09-R001-C01",
    "EU-01-R001-C01", "EU-01-R002-C01", "EU-01-R003-C01", "EU-01-R004-C01", "EU-01-R005-C01", "EU-01-R006-C01", "EU-01-R007-C01",
]


@pytest.fixture(scope="module")
def staged_chunks():
    """Load Step 5 staged chunks."""
    assert STAGING_CHUNKS_FILE.exists(), f"Staged chunks missing: {STAGING_CHUNKS_FILE}"
    with open(STAGING_CHUNKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [RegulatoryChunk(**item) for item in data]


@pytest.fixture(scope="module")
def staged_vector_store():
    """Create ChromaVectorStore instance for staging collection."""
    return ChromaVectorStore(
        persist_dir=STAGING_CHROMA_DIR,
        collection_name=STAGING_COLLECTION_NAME
    )


@pytest.fixture(scope="module")
def staged_collection_data(staged_vector_store):
    """Retrieve all data from the staged collection."""
    coll = staged_vector_store._get_collection()
    return coll.get(include=["metadatas", "documents", "embeddings"])


# ---------------------------------------------------------------------------
# 1. Directory and File Persistence Existence
# ---------------------------------------------------------------------------

def test_staging_chromadb_dir_and_files_exist():
    """Verify staging ChromaDB directory and sqlite database exist."""
    assert STAGING_CHROMA_DIR.exists()
    sqlite_file = STAGING_CHROMA_DIR / "chroma.sqlite3"
    assert sqlite_file.exists()
    assert sqlite_file.stat().st_size > 0


# ---------------------------------------------------------------------------
# 2. Vector Count and ID Uniqueness
# ---------------------------------------------------------------------------

def test_staging_collection_count_is_25(staged_vector_store):
    """Verify staging collection contains exactly 25 vectors."""
    stats = staged_vector_store.get_collection_stats()
    assert stats["total_vectors"] == 25
    assert stats["collection_name"] == STAGING_COLLECTION_NAME


def test_staging_chunk_id_uniqueness_and_naming(staged_collection_data):
    """Verify exactly 25 unique IDs matching the canonical 25 chunk IDs."""
    ids = staged_collection_data["ids"]
    assert len(ids) == 25
    assert len(set(ids)) == 25
    assert sorted(ids) == sorted(EXPECTED_CANONICAL_25_IDS)


# ---------------------------------------------------------------------------
# 3. Embedding Model, Dimensions & Finite Values
# ---------------------------------------------------------------------------

def test_embedding_dimensions_and_finite_values(staged_collection_data):
    """Verify strictly 384 dimensions and all finite float values (no NaN/Inf)."""
    embeddings = staged_collection_data["embeddings"]
    assert embeddings is not None
    assert len(embeddings) == 25

    for idx, emb in enumerate(embeddings):
        assert len(emb) == 384, f"Vector {idx} dimension is {len(emb)}, expected 384"
        assert all(isinstance(val, float) for val in emb)
        assert all(math.isfinite(val) for val in emb), f"Vector {idx} contains non-finite values (NaN or Inf)"


def test_embedding_manager_model_configuration():
    """Verify EmbeddingManager uses all-MiniLM-L6-v2 on CPU with 384 dimensions."""
    em = EmbeddingManager()
    assert em.model_name == "all-MiniLM-L6-v2"
    assert em.embedding_dimension == 384


# ---------------------------------------------------------------------------
# 4. Document Text & Non-Fabrication
# ---------------------------------------------------------------------------

def test_stored_documents_match_step5_chunks(staged_collection_data, staged_chunks):
    """Verify that stored ChromaDB documents strictly match Step 5 chunk.text."""
    chunk_map = {c.chunk_id: c for c in staged_chunks}
    ids = staged_collection_data["ids"]
    documents = staged_collection_data["documents"]

    for cid, doc in zip(ids, documents):
        assert cid in chunk_map
        expected_text = chunk_map[cid].text
        assert doc == expected_text
        assert doc.startswith("Source: ")


# ---------------------------------------------------------------------------
# 5. Metadata Integrity & Provenance Preservation
# ---------------------------------------------------------------------------

def test_metadata_preservation(staged_collection_data, staged_chunks):
    """Verify that all metadata fields are preserved in ChromaDB metadata."""
    chunk_map = {c.chunk_id: c for c in staged_chunks}
    ids = staged_collection_data["ids"]
    metadatas = staged_collection_data["metadatas"]

    for cid, meta in zip(ids, metadatas):
        chunk = chunk_map[cid]
        assert meta["chunk_id"] == chunk.chunk_id
        assert meta["record_id"] == chunk.record_id
        assert meta["source_id"] == chunk.source_id
        assert meta["jurisdiction"] == chunk.jurisdiction
        assert meta["authority_level"] == chunk.authority_level
        assert meta["section_article"] == chunk.section_article
        assert meta["title"] == chunk.title
        assert meta["official_source"] == chunk.official_source
        assert meta["official_source"].startswith("http")
        assert meta["text_type"] == "retrieval_text"


# ---------------------------------------------------------------------------
# 6. Candidate Gating Controls
# ---------------------------------------------------------------------------

def test_candidate_gating_preserved(staged_collection_data):
    """Verify that all 25 vectors are marked as candidates (0 approved)."""
    metadatas = staged_collection_data["metadatas"]
    assert len(metadatas) == 25

    approved_count = sum(1 for m in metadatas if m.get("is_approved_for_rag") is True)
    candidate_count = sum(1 for m in metadatas if m.get("is_approved_for_rag") is False)

    assert approved_count == 0
    assert candidate_count == 25

    for m in metadatas:
        assert m["validation_status"] in (
            "Candidate - Awaiting Approval",
            "Pending SME Validation",
            "Approved for RAG Integration - Pending SME Validation",
        )


# ---------------------------------------------------------------------------
# 7. Persistence & Reload Verification
# ---------------------------------------------------------------------------

def test_persistence_and_reload_fresh_client():
    """Verify that reopening a fresh chromadb.PersistentClient retrieves identical data."""
    fresh_client = chromadb.PersistentClient(path=str(STAGING_CHROMA_DIR))
    coll = fresh_client.get_collection(STAGING_COLLECTION_NAME)
    assert coll.count() == 25

    data = coll.get(include=["metadatas", "documents", "embeddings"])
    assert len(data["ids"]) == 25
    assert sorted(data["ids"]) == sorted(EXPECTED_CANONICAL_25_IDS)
    assert len(data["embeddings"]) == 25
    assert len(data["embeddings"][0]) == 384
    assert len(data["documents"]) == 25
    assert len(data["metadatas"]) == 25
    assert all(m["is_approved_for_rag"] is False for m in data["metadatas"])


# ---------------------------------------------------------------------------
# 8. Staged Retrieval Smoke Test
# ---------------------------------------------------------------------------

def test_staged_retrieval_smoke_test(staged_vector_store):
    """Verify that RegulatoryRetriever can query the staged store and return valid results."""
    retriever = RegulatoryRetriever(vector_store=staged_vector_store)

    # 1. Candidate-inclusive retrieval returns candidate results
    results = retriever.retrieve("bribery offence", top_k=3, filter_approved_only=False)
    assert len(results) == 3
    assert results[0].similarity_score > 0.50
    assert results[0].chunk_id.startswith("UK-01-")
    assert results[0].is_approved_for_rag is False

    # 2. Approved-only retrieval returns 0 results (fail-closed gate)
    approved_results = retriever.retrieve("bribery offence", top_k=3, filter_approved_only=True)
    assert len(approved_results) == 0


# ---------------------------------------------------------------------------
# 9. Active Store Immutability
# ---------------------------------------------------------------------------

def test_active_stores_immutability():
    """Verify that active production ChromaDB and processed JSON files remain 100% untouched."""
    # 1. Active ChromaDB check
    active_store = ChromaVectorStore(
        persist_dir=ACTIVE_CHROMA_DIR,
        collection_name=ACTIVE_COLLECTION_NAME
    )
    assert active_store._get_collection().count() == 15

    # 2. Active chunks check
    with open(ACTIVE_CHUNKS_FILE, "r", encoding="utf-8") as f:
        active_chunks = json.load(f)
    assert len(active_chunks) == 15

    # 3. Active normalized records check
    with open(ACTIVE_NORM_FILE, "r", encoding="utf-8") as f:
        active_norm = json.load(f)
    assert len(active_norm) == 15
