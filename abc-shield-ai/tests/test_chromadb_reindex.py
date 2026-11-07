"""Test suite for Embeddings & ChromaDB Re-indexing (Task W4.6).

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Collection exists and is named 'regulatory_records'
2. Collection count is exactly 15
3. Exactly 15 unique IDs
4. All expected Chunk_IDs exist (RR-UK-01-C01..09, RR-EU-01-C01..06)
5. No obsolete Week 3 IDs remain
6. Exactly 9 UK chunks + 6 EU chunks
7. Embedding dimension is strictly 384 across all vectors
8. All embeddings are present and non-empty
9. All embeddings have consistent 384-dimensional floating point vectors
10. Stored ChromaDB documents correspond strictly to canonical chunk text (retrieval_text)
11. Stored documents do not equal requirement paraphrase alone
12. text_type is 'retrieval_text' across all stored metadata
13. All Week 4 metadata fields are preserved in ChromaDB
14. retrieval_tags are stored as clean semicolon-delimited strings and semantically recoverable
15. All 15 vectors have validation_status == 'Candidate - Awaiting Approval'
16. All 15 vectors have is_approved_for_rag == False (0 approved)
17. Approved-only filter (filter_approved_only=True) returns 0 results
18. Candidate-inclusive retrieval (filter_approved_only=False) returns candidate results
19. UK jurisdiction filter returns strictly UK records
20. EU jurisdiction filter returns strictly EU records
21. Exact 1:1 chunk-to-vector alignment between regulatory_chunks.json and ChromaDB
22. PersistentClient reopen test: count, IDs, documents, embeddings, and metadata persist on disk
23. Existing RegulatoryRetriever can load the collection and execute queries
24. Retrieval smoke test executes successfully with valid scores and chunk IDs
25. Source artifact integrity: normalized_regulatory_records.json and regulatory_chunks.json unchanged
26. Raw Excel workbooks remain 100% unmodified (SHA-256 verification)
"""

from pathlib import Path
import hashlib
import json
import pytest
import chromadb

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult

PROCESSED_CHUNKS_PATH = Path("data/processed/regulatory_chunks.json")
NORMALIZED_RECORDS_PATH = Path("data/processed/normalized_regulatory_records.json")
CHROMA_PERSIST_DIR = Path("data/processed/chroma_db")
RAW_DATA_DIR = Path("data/raw")

NORMALIZED_RECORDS_EXPECTED_HASH = "5396480e563ce21de544184ba1f6789c8a974af2067c56a2249c21761ac6851d"
CHUNKS_EXPECTED_HASH = "05b07a06a1e04e3e62be4118e913361b736c746cd38e5ae21fc7bd1cecbb69ef"

RAW_EXCEL_EXPECTED_HASHES = {
    "ABC shield_Data Dictionary.xlsx": "57e9484826dd3bb3db71845d54e74db8e3a90fc4d504731d5bbec78e57ead2e6",
    "ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx": "2bab8181ef04d9643358d6e751117e414848cd01db82cfd33281f3b983fa6b5b",
    "ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx": "5a17ab6a3a883c1307c1e0a24cc1e94db705fee0b3aa6ff322d9cb6bee7f8e00",
    "ABC_Shield_Source_Register (1).xlsx": "0b6920636525ec871463ed458c285d61e4f50949a590a9e52b7dce41f0a7fa2b",
    "ABC_Shield_Source_Register_Reviewed (1).xlsx": "fde4d138f9cdd114304268ea6157d3cdaee60643789ff9f6fbdb54abfcf262c4",
}

EXPECTED_CHUNK_IDS = [
    "RR-UK-01-C01", "RR-UK-02-C01", "RR-UK-03-C01", "RR-UK-04-C01",
    "RR-UK-05-C01", "RR-UK-06-C01", "RR-UK-07-C01", "RR-UK-08-C01", "RR-UK-09-C01",
    "RR-EU-01-C01", "RR-EU-02-C01", "RR-EU-03-C01", "RR-EU-04-C01",
    "RR-EU-05-C01", "RR-EU-06-C01",
]


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


@pytest.fixture(scope="module")
def canonical_chunks():
    """Load canonical Week 4 chunks from disk."""
    assert PROCESSED_CHUNKS_PATH.exists(), f"File missing: {PROCESSED_CHUNKS_PATH}"
    with open(PROCESSED_CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [RegulatoryChunk(**item) for item in data]


@pytest.fixture(scope="module")
def persistent_chroma_client():
    """Create a persistent ChromaDB client for inspection."""
    assert CHROMA_PERSIST_DIR.exists(), f"ChromaDB directory missing: {CHROMA_PERSIST_DIR}"
    return chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))


@pytest.fixture(scope="module")
def regulatory_collection(persistent_chroma_client):
    """Retrieve the regulatory_records collection."""
    return persistent_chroma_client.get_collection("regulatory_records")


@pytest.fixture(scope="module")
def collection_data(regulatory_collection):
    """Retrieve all data from the collection including embeddings, documents, and metadatas."""
    return regulatory_collection.get(include=["metadatas", "documents", "embeddings"])


# ---------------------------------------------------------------------------
# 1. Collection Existence, Name, and Counts
# ---------------------------------------------------------------------------

def test_1_collection_exists_and_name(regulatory_collection):
    """Verify that collection exists and is named regulatory_records."""
    assert regulatory_collection is not None
    assert regulatory_collection.name == "regulatory_records"


def test_2_collection_count_is_15(regulatory_collection):
    """Verify that collection contains exactly 15 vectors."""
    assert regulatory_collection.count() == 15


def test_3_unique_ids(collection_data):
    """Verify that there are exactly 15 unique document IDs in the collection."""
    ids = collection_data["ids"]
    assert len(ids) == 15
    assert len(set(ids)) == 15


def test_4_all_expected_chunk_ids_present(collection_data):
    """Verify that all 15 canonical Chunk_IDs are present in ChromaDB."""
    ids = collection_data["ids"]
    assert sorted(ids) == sorted(EXPECTED_CHUNK_IDS)


def test_5_uk_and_eu_distribution(collection_data):
    """Verify exactly 9 UK chunks and 6 EU chunks."""
    ids = collection_data["ids"]
    uk_ids = [i for i in ids if "-UK-" in i]
    eu_ids = [i for i in ids if "-EU-" in i]
    assert len(uk_ids) == 9
    assert len(eu_ids) == 6


# ---------------------------------------------------------------------------
# 2. Embedding Model, Dimensions & Values
# ---------------------------------------------------------------------------

def test_6_embedding_dimension_is_384(collection_data):
    """Verify that all embeddings have dimension 384."""
    embeddings = collection_data["embeddings"]
    assert embeddings is not None
    assert len(embeddings) == 15
    for emb in embeddings:
        assert len(emb) == 384
        assert all(isinstance(val, float) for val in emb)


def test_7_embedding_manager_runtime_model_and_dimension():
    """Verify that EmbeddingManager uses all-MiniLM-L6-v2 and reports dimension 384."""
    em = EmbeddingManager()
    assert em.model_name == "all-MiniLM-L6-v2"
    assert em.embedding_dimension == 384


# ---------------------------------------------------------------------------
# 3. Document Text & Non-Fabrication
# ---------------------------------------------------------------------------

def test_8_stored_documents_match_canonical_chunk_text(collection_data, canonical_chunks):
    """Verify that every stored ChromaDB document strictly matches chunk.text (Retrieval_Text)."""
    canonical_map = {c.chunk_id: c for c in canonical_chunks}
    ids = collection_data["ids"]
    documents = collection_data["documents"]

    for cid, doc in zip(ids, documents):
        assert cid in canonical_map
        expected_text = canonical_map[cid].text
        assert doc == expected_text
        assert doc.startswith("Source: ")


def test_9_stored_documents_do_not_equal_requirement_alone(collection_data, canonical_chunks):
    """Verify that stored documents are not simply the requirement paraphrase alone."""
    canonical_map = {c.chunk_id: c for c in canonical_chunks}
    ids = collection_data["ids"]
    documents = collection_data["documents"]

    for cid, doc in zip(ids, documents):
        req = canonical_map[cid].requirement
        assert doc != req
        assert req in doc
        assert len(doc) > len(req)


# ---------------------------------------------------------------------------
# 4. Metadata Integrity & Week 4 Enriched Fields
# ---------------------------------------------------------------------------

def test_10_metadata_text_type_is_retrieval_text(collection_data):
    """Verify that text_type in stored metadata is 'retrieval_text' across all 15 records."""
    metadatas = collection_data["metadatas"]
    assert len(metadatas) == 15
    for meta in metadatas:
        assert meta["text_type"] == "retrieval_text"


def test_11_week_4_enriched_metadata_fields_present(collection_data):
    """Verify that all Week 4 enriched fields are present in ChromaDB metadata."""
    week4_fields = [
        "content_type", "retrieval_tags", "citation_label",
        "retrieval_priority", "authority_rule", "rag_instruction",
        "official_source_check_note",
    ]
    for meta in collection_data["metadatas"]:
        for field in week4_fields:
            assert field in meta, f"Field '{field}' missing from metadata"
            assert isinstance(meta[field], str)
            assert len(meta[field]) > 0


def test_12_retrieval_tags_semantically_recoverable(collection_data, canonical_chunks):
    """Verify that retrieval_tags stored as semicolon-delimited string can be recovered."""
    canonical_map = {c.chunk_id: c for c in canonical_chunks}
    for cid, meta in zip(collection_data["ids"], collection_data["metadatas"]):
        tags_str = meta["retrieval_tags"]
        recovered_tags = [t.strip() for t in tags_str.split(";") if t.strip()]
        expected_tags = canonical_map[cid].retrieval_tags
        assert recovered_tags == expected_tags


# ---------------------------------------------------------------------------
# 5. Approval & Gating Controls
# ---------------------------------------------------------------------------

def test_13_all_vectors_candidate_and_unapproved(collection_data):
    """Verify that all 15 vectors have validation_status Candidate and is_approved_for_rag False."""
    for meta in collection_data["metadatas"]:
        assert meta["validation_status"] == "Candidate - Awaiting Approval"
        assert meta["is_approved_for_rag"] is False


def test_14_approved_only_filter_returns_zero():
    """Verify that retriever with filter_approved_only=True returns exactly 0 results."""
    retriever = RegulatoryRetriever()
    results = retriever.retrieve("Bribery Act 2010", filter_approved_only=True, top_k=5)
    assert len(results) == 0


def test_15_candidate_inclusive_retrieval_returns_results():
    """Verify that retriever with filter_approved_only=False returns candidate results."""
    retriever = RegulatoryRetriever()
    results = retriever.retrieve("Bribery Act 2010", filter_approved_only=False, top_k=5)
    assert len(results) > 0
    assert all(r.is_approved_for_rag is False for r in results)
    assert all(r.validation_status == "Candidate - Awaiting Approval" for r in results)


# ---------------------------------------------------------------------------
# 6. Jurisdiction Filtering
# ---------------------------------------------------------------------------

def test_16_uk_jurisdiction_filtering():
    """Verify that jurisdiction='UK' returns strictly UK records without cross-contamination."""
    retriever = RegulatoryRetriever()
    results = retriever.retrieve("offence", jurisdiction="UK", top_k=5)
    assert len(results) > 0
    assert all(r.jurisdiction == "UK" for r in results)
    assert all(r.chunk_id.startswith("RR-UK-") for r in results)


def test_17_eu_jurisdiction_filtering():
    """Verify that jurisdiction='EU' returns strictly EU records without cross-contamination."""
    retriever = RegulatoryRetriever()
    results = retriever.retrieve("offence", jurisdiction="EU", top_k=5)
    assert len(results) > 0
    assert all(r.jurisdiction == "EU" for r in results)
    assert all(r.chunk_id.startswith("RR-EU-") for r in results)


# ---------------------------------------------------------------------------
# 7. Persistence Reopen Test
# ---------------------------------------------------------------------------

def test_18_persistent_client_reopen_integrity():
    """Verify that reopening a fresh PersistentClient retrieves identical vectors and metadata."""
    fresh_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    coll = fresh_client.get_collection("regulatory_records")
    assert coll.count() == 15

    data = coll.get(include=["metadatas", "documents", "embeddings"])
    assert len(data["ids"]) == 15
    assert sorted(data["ids"]) == sorted(EXPECTED_CHUNK_IDS)
    assert len(data["embeddings"]) == 15
    assert len(data["embeddings"][0]) == 384
    assert len(data["documents"]) == 15
    assert all(d.startswith("Source: ") for d in data["documents"])
    assert len(data["metadatas"]) == 15
    assert all(m["is_approved_for_rag"] is False for m in data["metadatas"])


# ---------------------------------------------------------------------------
# 8. Retrieval Smoke Test
# ---------------------------------------------------------------------------

def test_19_retrieval_smoke_test():
    """Smoke test: execute a realistic query and confirm result structure and scores."""
    retriever = RegulatoryRetriever()
    query = "What does the Bribery Act 2010 say about bribing another person?"
    results = retriever.retrieve(query, top_k=3)

    assert len(results) == 3
    top_result = results[0]
    assert isinstance(top_result, RetrievalResult)
    assert top_result.chunk_id == "RR-UK-01-C01"
    assert top_result.similarity_score > 0.70
    assert top_result.distance >= 0.0
    assert top_result.text.startswith("Source: ")
    assert top_result.validation_status == "Candidate - Awaiting Approval"
    assert top_result.is_approved_for_rag is False


# ---------------------------------------------------------------------------
# 9. Source Artifact & Raw Workbook Immutability
# ---------------------------------------------------------------------------

def test_20_normalized_records_unmodified():
    """Verify that normalized_regulatory_records.json was not modified during indexing."""
    assert NORMALIZED_RECORDS_PATH.exists()
    current_hash = compute_file_hash(NORMALIZED_RECORDS_PATH)
    assert current_hash == NORMALIZED_RECORDS_EXPECTED_HASH, (
        f"normalized_regulatory_records.json modified! Expected {NORMALIZED_RECORDS_EXPECTED_HASH}, got {current_hash}"
    )


def test_21_regulatory_chunks_unmodified():
    """Verify that regulatory_chunks.json was not modified during indexing."""
    assert PROCESSED_CHUNKS_PATH.exists()
    current_hash = compute_file_hash(PROCESSED_CHUNKS_PATH)
    assert current_hash == CHUNKS_EXPECTED_HASH, (
        f"regulatory_chunks.json modified! Expected {CHUNKS_EXPECTED_HASH}, got {current_hash}"
    )


def test_22_raw_excel_workbooks_unmodified():
    """Verify that all 5 raw Excel workbooks remain 100% untouched."""
    for filename, expected_hash in RAW_EXCEL_EXPECTED_HASHES.items():
        filepath = RAW_DATA_DIR / filename
        assert filepath.exists(), f"File missing: {filename}"
        current_hash = compute_file_hash(filepath)
        assert current_hash == expected_hash, (
            f"Raw workbook {filename} modified! Expected {expected_hash}, got {current_hash}"
        )
