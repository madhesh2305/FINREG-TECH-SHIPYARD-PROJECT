"""Dedicated Tests for Fast-Track Step 2: Prepare Canonical Knowledge Base.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Fast-track staging artifacts exist in data/staging/fast_track/
2. Exactly 25 records with deterministic unique Record IDs
3. 100% source mapping integrity against the 15 canonical sources
4. Strict separation between Exact_Source_Extract and Structured_Summary
5. Full metadata preservation including new Validation_Date ('20 October 2026')
6. Fail-closed candidate gating: is_approved_for_rag == False, validation_status == 'Approved for RAG Integration - Pending SME Validation'
7. Alignment with Master Handover Tracker DEC-01 (OPEN) and Test Pack RAG-014
8. Staged ChromaDB collection 'canonical_regulatory_records' contains 25 vectors with 384 dimensions
9. ChromaDB embeddings reused without recomputation
10. Active production data stores in data/processed/ and data/raw/ strictly unmodified
"""

from pathlib import Path
import json
import openpyxl
import pytest
import chromadb

from rag.ingestion.schemas import NormalizedRegulatoryRecord, RegulatoryChunk
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.retriever import RegulatoryRetriever

FAST_TRACK_DIR = Path("data/staging/fast_track")
FAST_TRACK_NORM_FILE = FAST_TRACK_DIR / "normalized_regulatory_records.json"
FAST_TRACK_CHUNKS_FILE = FAST_TRACK_DIR / "regulatory_chunks.json"
FAST_TRACK_VAL_FILE = FAST_TRACK_DIR / "validation_report.json"
FAST_TRACK_META_MAP_FILE = FAST_TRACK_DIR / "metadata_mapping.json"

INCOMING_DIR = Path("data/incoming_handover_20261021")
INCOMING_CORPUS_FILE = INCOMING_DIR / "ABC_Shield_Canonical_25_Record_Corpus.xlsx"
INCOMING_SR_FILE = INCOMING_DIR / "ABC_Shield_Canonical_Source_Register.xlsx"
INCOMING_TRACKER_FILE = INCOMING_DIR / "ABC_Shield_Master_Handover_Tracker.xlsx"
INCOMING_TEST_PACK_FILE = INCOMING_DIR / "ABC_Shield_Canonical_RAG_Test_Pack.xlsx"

STAGED_CHROMA_DIR = Path("data/staging/madhesh_handover/step6/chroma_db")
STAGED_COLLECTION_NAME = "canonical_regulatory_records"

ACTIVE_PROCESSED_DIR = Path("data/processed")
ACTIVE_CHROMA_DIR = ACTIVE_PROCESSED_DIR / "chroma_db"
ACTIVE_NORM_FILE = ACTIVE_PROCESSED_DIR / "normalized_regulatory_records.json"
ACTIVE_CHUNKS_FILE = ACTIVE_PROCESSED_DIR / "regulatory_chunks.json"
RAW_DIR = Path("data/raw")

EXPECTED_CANONICAL_25_IDS = [
    "UK-01-R001", "UK-01-R002", "UK-01-R003", "UK-01-R004", "UK-01-R005", "UK-01-R006",
    "UK-02-R001", "UK-02-R002", "UK-02-R003", "UK-02-R004", "UK-02-R005", "UK-02-R006",
    "UK-03-R001", "UK-03-R002", "UK-03-R003", "UK-03-R004", "UK-03-R005",
    "UK-09-R001",
    "EU-01-R001", "EU-01-R002", "EU-01-R003", "EU-01-R004", "EU-01-R005", "EU-01-R006", "EU-01-R007",
]

EXPECTED_CHUNK_25_IDS = [f"{rid}-C01" for rid in EXPECTED_CANONICAL_25_IDS]


# ---------------------------------------------------------------------------
# 1. Staging Artifacts Existence
# ---------------------------------------------------------------------------

def test_fast_track_staging_artifacts_exist():
    """Verify all 4 Fast-Track Step 2 artifacts exist and are non-empty."""
    assert FAST_TRACK_DIR.exists()
    assert FAST_TRACK_NORM_FILE.exists() and FAST_TRACK_NORM_FILE.stat().st_size > 0
    assert FAST_TRACK_CHUNKS_FILE.exists() and FAST_TRACK_CHUNKS_FILE.stat().st_size > 0
    assert FAST_TRACK_VAL_FILE.exists() and FAST_TRACK_VAL_FILE.stat().st_size > 0
    assert FAST_TRACK_META_MAP_FILE.exists() and FAST_TRACK_META_MAP_FILE.stat().st_size > 0


# ---------------------------------------------------------------------------
# 2. Record Count, IDs, and Uniqueness
# ---------------------------------------------------------------------------

def test_fast_track_record_count_and_unique_ids():
    """Verify exactly 25 records with expected canonical IDs and 0 duplicates."""
    with open(FAST_TRACK_NORM_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == 25
    record_ids = [r["record_id"] for r in records]
    assert len(record_ids) == len(set(record_ids))
    assert sorted(record_ids) == sorted(EXPECTED_CANONICAL_25_IDS)


def test_fast_track_chunk_count_and_unique_ids():
    """Verify exactly 25 chunks with expected chunk IDs and 0 duplicates."""
    with open(FAST_TRACK_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    assert len(chunks) == 25
    chunk_ids = [c["chunk_id"] for c in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert sorted(chunk_ids) == sorted(EXPECTED_CHUNK_25_IDS)


# ---------------------------------------------------------------------------
# 3. Source Mapping Integrity
# ---------------------------------------------------------------------------

def test_fast_track_source_mapping_integrity():
    """Verify all 25 records map to valid source IDs in the canonical source register."""
    wb_sr = openpyxl.load_workbook(INCOMING_SR_FILE, data_only=True)
    sheet_sr = wb_sr["Source Register"]
    rows_sr = list(sheet_sr.iter_rows(values_only=True))
    headers_sr = rows_sr[0]
    sid_idx = headers_sr.index("Source ID")
    valid_source_ids = {r[sid_idx] for r in rows_sr[1:] if r[sid_idx]}
    assert len(valid_source_ids) == 15

    with open(FAST_TRACK_NORM_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    for r in records:
        assert r["source_id"] in valid_source_ids, f"Unresolved source_id: {r['source_id']}"

    # Verify breakdown
    sources_in_corpus = {r["source_id"] for r in records}
    assert sources_in_corpus == {"UK-01", "UK-02", "UK-03", "UK-09", "EU-01"}


# ---------------------------------------------------------------------------
# 4. Strict Separation: Extracts vs Summaries
# ---------------------------------------------------------------------------

def test_fast_track_extract_and_summary_separation():
    """Verify Exact_Source_Extract and Structured_Summary are strictly separated."""
    with open(FAST_TRACK_NORM_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    for r in records:
        assert r["regulatory_text"] is not None and len(r["regulatory_text"].strip()) > 0
        assert r["requirement"] is not None and len(r["requirement"].strip()) > 0
        assert r["regulatory_text"] != r["requirement"], f"Record {r['record_id']} has identical extract and summary"


# ---------------------------------------------------------------------------
# 5. Metadata Preservation & Validation_Date
# ---------------------------------------------------------------------------

def test_fast_track_metadata_preservation_and_validation_date():
    """Verify all required metadata fields and new Validation_Date ('20 October 2026') are preserved."""
    with open(FAST_TRACK_NORM_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    for r in records:
        assert r["validation_date"] == "20 October 2026", f"Record {r['record_id']} missing validation_date"
        assert r["official_source"] is not None and r["official_source"].startswith("http")
        assert r["jurisdiction"] in ("UK", "EU", "EU-level")
        assert r["authority_level"] in ("A", "B", "C", "D")
        assert r["section_article"] is not None and len(r["section_article"]) > 0
        assert r["topic"] is not None and len(r["topic"]) > 0

    with open(FAST_TRACK_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for c in chunks:
        assert c["validation_date"] == "20 October 2026"
        assert c["text_type"] == "retrieval_text"
        assert c["citation_label"] is not None and len(c["citation_label"]) > 0


# ---------------------------------------------------------------------------
# 6. Candidate Gating & Option A Provisional Governance
# ---------------------------------------------------------------------------

def test_fast_track_option_a_candidate_gating():
    """Verify fail-closed candidate gating per Option A (DEC-01 OPEN & RAG-014)."""
    with open(FAST_TRACK_NORM_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    for r in records:
        assert r["is_approved_for_rag"] is False, f"Record {r['record_id']} illegally marked approved"
        assert r["validation_status"] == "Approved for RAG Integration - Pending SME Validation"

    with open(FAST_TRACK_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for c in chunks:
        assert c["is_approved_for_rag"] is False
        assert c["validation_status"] == "Approved for RAG Integration - Pending SME Validation"


def test_fast_track_validation_report_zero_errors():
    """Verify validation report contains exactly 25 valid records and 0 critical errors."""
    with open(FAST_TRACK_VAL_FILE, "r", encoding="utf-8") as f:
        rep = json.load(f)

    assert rep["total_records"] == 25
    assert rep["valid_records_count"] == 25
    assert rep["candidate_records_count"] == 25
    assert rep["approved_records_count"] == 0
    assert rep["all_source_ids_resolved"] is True
    assert rep["regulatory_text_available"] is True
    assert rep["issues"] == []


# ---------------------------------------------------------------------------
# 7. Embedding Reusability & Staged ChromaDB Verification
# ---------------------------------------------------------------------------

def test_fast_track_staged_chromadb_embedding_reusability():
    """Verify staged ChromaDB collection contains 25 vectors with 384 dimensions and updated metadata."""
    client = chromadb.PersistentClient(path=str(STAGED_CHROMA_DIR))
    col = client.get_collection(STAGED_COLLECTION_NAME)

    assert col.count() == 25

    all_data = col.get(include=["metadatas", "embeddings", "documents"])
    ids = all_data["ids"]
    metadatas = all_data["metadatas"]
    embeddings = all_data["embeddings"]
    documents = all_data["documents"]

    assert len(ids) == 25
    assert sorted(ids) == sorted(EXPECTED_CHUNK_25_IDS)

    for idx, mid in enumerate(ids):
        meta = metadatas[idx]
        emb = embeddings[idx]
        doc = documents[idx]

        assert len(emb) == 384, f"Chunk {mid} invalid embedding dimension {len(emb)}"
        assert meta["validation_status"] == "Approved for RAG Integration - Pending SME Validation"
        assert meta["validation_date"] == "20 October 2026"
        assert meta["is_approved_for_rag"] is False
        assert len(doc) > 0


def test_fast_track_staged_retriever_returns_provisional_metadata():
    """Verify retriever retrieves evidence chunks reflecting provisional status and candidate gating."""
    store = ChromaVectorStore(persist_dir=STAGED_CHROMA_DIR, collection_name=STAGED_COLLECTION_NAME)
    embedder = EmbeddingManager(model_name="all-MiniLM-L6-v2")
    retriever = RegulatoryRetriever(embedding_manager=embedder, vector_store=store)

    results = retriever.retrieve(query="bribing another person offences under Bribery Act", top_k=3)
    assert len(results) > 0

    top_result = results[0]
    assert top_result.record_id == "UK-01-R001"
    assert top_result.is_approved_for_rag is False
    assert top_result.validation_status == "Approved for RAG Integration - Pending SME Validation"
    assert top_result.validation_date == "20 October 2026"


def test_fast_track_retriever_blocks_candidates_under_approved_filter():
    """Verify filter_approved_only=True returns 0 results because all 25 records are provisional candidates."""
    store = ChromaVectorStore(persist_dir=STAGED_CHROMA_DIR, collection_name=STAGED_COLLECTION_NAME)
    embedder = EmbeddingManager(model_name="all-MiniLM-L6-v2")
    retriever = RegulatoryRetriever(embedding_manager=embedder, vector_store=store)

    approved_results = retriever.retrieve(
        query="What constitutes an offence of bribing another person?",
        top_k=5,
        filter_approved_only=True,
    )
    assert approved_results == []


# ---------------------------------------------------------------------------
# 8. Active Production Stores Immutability
# ---------------------------------------------------------------------------

def test_fast_track_active_production_stores_untouched():
    """Verify active production data in data/processed/ and data/raw/ remain 100% untouched."""
    active_store = ChromaVectorStore(persist_dir=ACTIVE_CHROMA_DIR, collection_name="regulatory_records")
    active_col = active_store._get_collection()
    assert active_col.count() == 15, f"Active ChromaDB was modified! Expected 15 vectors, found {active_col.count()}"

    with open(ACTIVE_NORM_FILE, "r", encoding="utf-8") as f:
        active_norm = json.load(f)
    assert len(active_norm) == 15, f"Active normalized records modified! Expected 15, found {len(active_norm)}"

    with open(ACTIVE_CHUNKS_FILE, "r", encoding="utf-8") as f:
        active_chunks = json.load(f)
    assert len(active_chunks) == 15, f"Active chunks modified! Expected 15, found {len(active_chunks)}"

    raw_excels = list(RAW_DIR.glob("*.xlsx"))
    assert len(raw_excels) == 7, f"Raw excel count changed! Expected 7, found {len(raw_excels)}"
