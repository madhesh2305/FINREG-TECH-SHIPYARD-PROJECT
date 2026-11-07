"""ABC Shield — Fast-Track Step 2: Prepare Canonical Knowledge Base.

Loads canonical 25-record corpus from data/incoming_handover_20261021/,
normalizes with provisional governance (Option A: DEC-01 OPEN / RAG-014),
validates schema and distinction between verbatim extracts and summaries,
generates canonical chunks, preserves vector embeddings, and deterministically
updates staged ChromaDB metadata without recomputing embeddings.

Ensures active production stores in data/processed/ and data/raw/ remain 100% untouched.
"""

from pathlib import Path
import json
import logging
import sys
import hashlib

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.ingestion.excel_loader import ExcelWorkbookLoader
from rag.ingestion.normalizer import RegulatoryDataNormalizer
from rag.ingestion.validator import RegulatoryDataValidator
from rag.ingestion.chunker import RegulatoryRecordChunker
from rag.retrieval.vector_store import ChromaVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INCOMING_DIR = Path("data/incoming_handover_20261021")
INCOMING_CORPUS_FILE = INCOMING_DIR / "ABC_Shield_Canonical_25_Record_Corpus.xlsx"
INCOMING_SR_FILE = INCOMING_DIR / "ABC_Shield_Canonical_Source_Register.xlsx"

FAST_TRACK_STAGING_DIR = Path("data/staging/fast_track")
STAGED_CHROMA_DIR = Path("data/staging/madhesh_handover/step6/chroma_db")
STAGED_COLLECTION_NAME = "canonical_regulatory_records"

PROCESSED_CHROMA_DIR = Path("data/processed/chroma_db")
PROCESSED_COLLECTION_NAME = "regulatory_records"
PROCESSED_NORM_FILE = Path("data/processed/normalized_regulatory_records.json")
PROCESSED_CHUNKS_FILE = Path("data/processed/regulatory_chunks.json")


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_prepare_fast_track_kb():
    logger.info("=== Fast-Track Step 2: Preparing Canonical Knowledge Base ===")

    # 1. Capture active production baseline hashes
    active_norm_hash_before = sha256_file(PROCESSED_NORM_FILE) if PROCESSED_NORM_FILE.exists() else None
    active_chunks_hash_before = sha256_file(PROCESSED_CHUNKS_FILE) if PROCESSED_CHUNKS_FILE.exists() else None
    active_store = ChromaVectorStore(persist_dir=PROCESSED_CHROMA_DIR, collection_name=PROCESSED_COLLECTION_NAME)
    active_vectors_before = active_store._get_collection().count()
    logger.info(f"Active production baseline: {active_vectors_before} vectors in {PROCESSED_COLLECTION_NAME}")

    # 2. Load incoming raw files
    loader = ExcelWorkbookLoader(
        raw_data_dir=INCOMING_DIR,
        regulatory_records_path=INCOMING_CORPUS_FILE,
        source_register_path=INCOMING_SR_FILE,
    )
    raw_records = loader.load_regulatory_records_raw()
    sources = loader.load_source_register()

    logger.info(f"Loaded {len(raw_records)} raw records and {len(sources)} sources from {INCOMING_DIR}")
    assert len(raw_records) == 25, f"Expected 25 raw records, found {len(raw_records)}"
    assert len(sources) == 15, f"Expected 15 sources, found {len(sources)}"

    # 3. Normalize records with Option A governance
    normalizer = RegulatoryDataNormalizer(source_register=sources)
    normalized_records = normalizer.normalize_all(raw_records)
    logger.info(f"Normalized {len(normalized_records)} records")

    # 4. Validate records
    validator = RegulatoryDataValidator(source_register=sources)
    validation_report = validator.validate_records(normalized_records)
    logger.info(
        f"Validation: total={validation_report.total_records}, "
        f"valid={validation_report.valid_records_count}, "
        f"candidate={validation_report.candidate_records_count}, "
        f"approved={validation_report.approved_records_count}, "
        f"critical_errors={validation_report.has_critical_errors}"
    )
    assert validation_report.total_records == 25
    assert validation_report.valid_records_count == 25
    assert validation_report.candidate_records_count == 25
    assert validation_report.approved_records_count == 0
    assert not validation_report.has_critical_errors

    # 5. Generate chunks
    chunker = RegulatoryRecordChunker(max_chunk_chars=800, overlap_chars=100)
    chunks = chunker.chunk_all(normalized_records)
    logger.info(f"Generated {len(chunks)} chunks from 25 records")
    assert len(chunks) == 25, f"Expected 25 chunks, got {len(chunks)}"

    # 6. Save Fast-Track staging artifacts
    FAST_TRACK_STAGING_DIR.mkdir(parents=True, exist_ok=True)

    norm_json_path = FAST_TRACK_STAGING_DIR / "normalized_regulatory_records.json"
    with open(norm_json_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in normalized_records], f, indent=2, ensure_ascii=False)
    logger.info(f"Saved normalized records to {norm_json_path}")

    chunks_json_path = FAST_TRACK_STAGING_DIR / "regulatory_chunks.json"
    with open(chunks_json_path, "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in chunks], f, indent=2, ensure_ascii=False)
    logger.info(f"Saved chunks to {chunks_json_path}")

    val_report_path = FAST_TRACK_STAGING_DIR / "validation_report.json"
    with open(val_report_path, "w", encoding="utf-8") as f:
        json.dump(validation_report.model_dump(), f, indent=2, ensure_ascii=False)
    logger.info(f"Saved validation report to {val_report_path}")

    # 7. Construct and persist deterministic metadata mapping
    metadata_mapping = {}
    for c in chunks:
        meta = ChromaVectorStore._sanitize_metadata(c)
        metadata_mapping[c.chunk_id] = {
            "record_id": c.record_id,
            "source_id": c.source_id,
            "section_article": c.section_article,
            "topic": c.topic,
            "official_source": c.official_source,
            "validation_status": c.validation_status,
            "validation_date": c.validation_date,
            "is_approved_for_rag": c.is_approved_for_rag,
            "text_type": c.text_type,
            "retrieval_text_preview": c.text[:120] + "...",
            "governance_note": "Option A provisional RAG integration; final compliance SME validation pending per Master Handover Tracker DEC-01 (OPEN)",
        }

    meta_map_path = FAST_TRACK_STAGING_DIR / "metadata_mapping.json"
    with open(meta_map_path, "w", encoding="utf-8") as f:
        json.dump(metadata_mapping, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved metadata mapping to {meta_map_path}")

    # 8. Update metadata in Staged ChromaDB without recomputing embeddings
    staged_store = ChromaVectorStore(
        persist_dir=STAGED_CHROMA_DIR,
        collection_name=STAGED_COLLECTION_NAME,
    )
    staged_col = staged_store._get_collection()
    staged_count = staged_col.count()
    logger.info(f"Staged ChromaDB collection '{STAGED_COLLECTION_NAME}' vector count: {staged_count}")
    assert staged_count == 25, f"Expected 25 vectors in staged collection, found {staged_count}"

    # Perform metadata update
    ids_to_update = [c.chunk_id for c in chunks]
    metadatas_to_update = [ChromaVectorStore._sanitize_metadata(c) for c in chunks]
    staged_col.update(
        ids=ids_to_update,
        metadatas=metadatas_to_update,
    )
    logger.info(f"Updated metadata on {len(ids_to_update)} vectors in collection '{STAGED_COLLECTION_NAME}' without re-embedding")

    # Verify reload of updated metadata
    sample_res = staged_col.get(ids=["UK-01-R001-C01"], include=["metadatas", "embeddings"])
    sample_meta = sample_res["metadatas"][0]
    sample_emb = sample_res["embeddings"][0]
    logger.info(f"Sample UK-01-R001-C01 validation_status: {sample_meta['validation_status']}")
    logger.info(f"Sample UK-01-R001-C01 validation_date: {sample_meta['validation_date']}")
    logger.info(f"Sample UK-01-R001-C01 is_approved_for_rag: {sample_meta['is_approved_for_rag']}")
    logger.info(f"Sample UK-01-R001-C01 embedding dimension preserved: {len(sample_emb)}")
    assert sample_meta["validation_status"] == "Approved for RAG Integration - Pending SME Validation"
    assert sample_meta["validation_date"] == "20 October 2026"
    assert sample_meta["is_approved_for_rag"] is False
    assert len(sample_emb) == 384

    # 9. Verify Active Stores Immutability
    active_norm_hash_after = sha256_file(PROCESSED_NORM_FILE) if PROCESSED_NORM_FILE.exists() else None
    active_chunks_hash_after = sha256_file(PROCESSED_CHUNKS_FILE) if PROCESSED_CHUNKS_FILE.exists() else None
    active_vectors_after = active_store._get_collection().count()

    assert active_norm_hash_before == active_norm_hash_after, "Active normalized records file was modified!"
    assert active_chunks_hash_before == active_chunks_hash_after, "Active chunks file was modified!"
    assert active_vectors_before == active_vectors_after, f"Active vectors count changed: {active_vectors_before} -> {active_vectors_after}"
    logger.info("Active production stores verified 100% untouched!")

    summary = {
        "status": "SUCCESS",
        "raw_records_processed": len(raw_records),
        "sources_processed": len(sources),
        "normalized_records_count": len(normalized_records),
        "chunks_generated": len(chunks),
        "validation_report": {
            "total_records": validation_report.total_records,
            "valid_records": validation_report.valid_records_count,
            "candidate_records": validation_report.candidate_records_count,
            "approved_records": validation_report.approved_records_count,
            "critical_errors": validation_report.has_critical_errors,
        },
        "option_a_governance": {
            "validation_status": "Approved for RAG Integration - Pending SME Validation",
            "validation_date": "20 October 2026",
            "is_approved_for_rag": False,
            "tracker_decision": "DEC-01 OPEN",
            "test_case_alignment": "RAG-014",
        },
        "chromadb_staging": {
            "persist_dir": str(STAGED_CHROMA_DIR),
            "collection_name": STAGED_COLLECTION_NAME,
            "vector_count": staged_count,
            "embeddings_reused_without_recomputation": True,
            "metadata_updated": True,
        },
        "active_production_stores_untouched": {
            "processed_chromadb_vectors": active_vectors_after,
            "processed_records_hash_intact": True,
            "processed_chunks_hash_intact": True,
        },
    }
    print("\n--- FAST-TRACK STEP 2 KNOWLEDGE BASE PREPARATION SUMMARY ---")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    run_prepare_fast_track_kb()
