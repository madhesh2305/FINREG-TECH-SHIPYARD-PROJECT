"""Tests for Step 5: Canonical Chunk Generation and Validation in Staging.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Verifies:
1. Staged chunks file exists in data/staging/madhesh_handover/step5/regulatory_chunks.json
2. Exactly 25 chunks generated from 25 normalized records
3. Deterministic and unique Chunk_IDs matching {Record_ID}-C01
4. 100% parent record and source ID traceability on every chunk
5. Preservation of official URLs, section/article, jurisdiction, authority level, and topic
6. Exact extract and requirement separation preserved (no silent substitution)
7. Chunk text within configured max_chunk_chars bounds (<= 800 chars)
8. Candidate gating: 25 Candidate / 0 Approved (is_approved_for_rag = False)
9. Active processed files and ChromaDB remain 100% unmodified (15 records, 15 chunks, 15 vectors)
"""

from pathlib import Path
import json
import pytest

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.vector_store import ChromaVectorStore

STAGING_STEP5_DIR = Path("data/staging/madhesh_handover/step5")
STAGED_CHUNKS_FILE = STAGING_STEP5_DIR / "regulatory_chunks.json"

PROCESSED_DIR = Path("data/processed")


def test_staged_chunks_file_exists():
    """Verify staged chunks JSON exists and has non-zero size."""
    assert STAGING_STEP5_DIR.exists()
    assert STAGED_CHUNKS_FILE.exists()
    assert STAGED_CHUNKS_FILE.stat().st_size > 0


def test_staged_chunk_count_and_id_uniqueness():
    """Verify exactly 25 chunks exist with unique, non-empty deterministic IDs."""
    with open(STAGED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    assert len(chunks_data) == 25
    chunk_ids = [c["chunk_id"] for c in chunks_data]

    # No duplicates
    assert len(chunk_ids) == len(set(chunk_ids))

    # All match convention {Record_ID}-C01
    for c in chunks_data:
        cid = c["chunk_id"]
        rid = c["record_id"]
        assert cid.startswith(rid)
        assert cid.endswith("-C01")


def test_parent_record_and_source_traceability():
    """Verify every chunk traces back to its valid parent Record_ID and Source_ID."""
    with open(STAGED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    expected_sources = {"UK-01", "UK-02", "UK-03", "UK-09", "EU-01"}
    for c in chunks_data:
        assert c["record_id"] is not None and len(c["record_id"]) > 0
        assert c["source_id"] in expected_sources
        assert c["chunk_index"] == 0
        assert c["total_chunks"] == 1


def test_chunk_text_length_and_boundary_rules():
    """Verify chunk text is non-empty and does not exceed max_chunk_chars (800)."""
    with open(STAGED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    for c in chunks_data:
        text = c["text"]
        assert len(text.strip()) > 50  # meaningful content
        assert len(text) <= 800  # max_chunk_chars
        assert c["text_type"] == "retrieval_text"


def test_chunk_metadata_preservation():
    """Verify metadata hierarchy (URLs, jurisdiction, authority level, section) is preserved."""
    with open(STAGED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    for c in chunks_data:
        assert str(c["official_source"]).startswith("http")
        assert c["jurisdiction"] in ("UK", "EU", "EU-level")
        assert c["authority_level"] in ("A", "B", "C", "D")
        assert c["section_article"] is not None and len(c["section_article"].strip()) > 0
        assert c["title"] is not None and len(c["title"].strip()) > 0


def test_text_separation_preserved_on_chunks():
    """Verify requirement and regulatory_text remain distinct without silent substitution."""
    with open(STAGED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    for c in chunks_data:
        assert c["requirement"] is not None and len(c["requirement"].strip()) > 0
        assert c["regulatory_text"] is not None and len(c["regulatory_text"].strip()) > 0
        assert c["requirement"] != c["regulatory_text"]


def test_candidate_gating_preserved_across_all_chunks():
    """Verify fail-closed gating: 25 Candidate / 0 Approved."""
    with open(STAGED_CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    assert sum(1 for c in chunks_data if c.get("is_approved_for_rag") is True) == 0
    assert sum(1 for c in chunks_data if c.get("is_approved_for_rag") is False) == 25

    for c in chunks_data:
        assert c.get("validation_status") in ("Candidate - Awaiting Approval", "Pending SME Validation")


def test_active_processed_data_and_chromadb_immutability():
    """Verify active processed JSON and active ChromaDB remain strictly untouched at 15 items."""
    norm_path = PROCESSED_DIR / "normalized_regulatory_records.json"
    chunk_path = PROCESSED_DIR / "regulatory_chunks.json"

    with open(norm_path, "r", encoding="utf-8") as f:
        norm_data = json.load(f)
    with open(chunk_path, "r", encoding="utf-8") as f:
        chunk_data = json.load(f)

    assert len(norm_data) == 15
    assert len(chunk_data) == 15

    chroma_store = ChromaVectorStore(persist_dir=PROCESSED_DIR / "chroma_db")
    assert chroma_store._get_collection().count() == 15
