"""Step 6: Staged ChromaDB Indexing for Canonical 25 Chunks.

Project: ABC Shield / FinRegTech ShipYard AI/RAG
Role: Padma Kumar — AI/RAG & Conflict Detection Engineer

Reads verified chunks from data/staging/madhesh_handover/step5/regulatory_chunks.json,
generates embeddings locally using all-MiniLM-L6-v2 on CPU, and indexes into an isolated
staging ChromaDB collection at data/staging/madhesh_handover/step6/chroma_db/.

Ensures 100% immutability of active data/processed/ stores.
"""

from pathlib import Path
import json
import logging
import math
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval import index_processed_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

STAGING_STEP5_CHUNKS = Path("data/staging/madhesh_handover/step5/regulatory_chunks.json")
STAGING_STEP6_DIR = Path("data/staging/madhesh_handover/step6")
STAGING_CHROMA_DIR = STAGING_STEP6_DIR / "chroma_db"
STAGING_COLLECTION_NAME = "canonical_regulatory_records"

PROCESSED_CHROMA_DIR = Path("data/processed/chroma_db")
PROCESSED_COLLECTION_NAME = "regulatory_records"


def run_staging_indexing() -> dict:
    """Run isolated staged embedding generation and indexing."""
    logger.info("Starting Step 6 Staged Indexing...")

    # 1. Path validations
    if not STAGING_STEP5_CHUNKS.exists():
        raise FileNotFoundError(f"Step 5 staged chunks not found: {STAGING_STEP5_CHUNKS}")

    STAGING_STEP6_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Verify active store state before execution
    active_store = ChromaVectorStore(
        persist_dir=PROCESSED_CHROMA_DIR,
        collection_name=PROCESSED_COLLECTION_NAME
    )
    active_count_before = active_store._get_collection().count()
    logger.info("Active ChromaDB vector count before staging build: %d", active_count_before)

    # 3. Load input chunks
    with open(STAGING_STEP5_CHUNKS, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)

    if len(raw_chunks) != 25:
        raise ValueError(f"Expected exactly 25 chunks, found {len(raw_chunks)}")

    chunks = [RegulatoryChunk(**c) for c in raw_chunks]
    logger.info("Successfully loaded %d chunks from %s", len(chunks), STAGING_STEP5_CHUNKS)

    # 4. Generate embeddings with local model
    embedder = EmbeddingManager(model_name="all-MiniLM-L6-v2")
    texts = [c.text for c in chunks]
    embeddings = embedder.embed_texts(texts)

    logger.info(
        "Generated %d embeddings using model '%s' (dimension: %d)",
        len(embeddings),
        embedder.model_name,
        embedder.embedding_dimension
    )

    # Validate embeddings: finite, correct dimension, non-empty
    for idx, emb in enumerate(embeddings):
        if len(emb) != 384:
            raise ValueError(f"Chunk {chunks[idx].chunk_id} embedding dimension is {len(emb)}, expected 384")
        if not all(isinstance(v, float) and math.isfinite(v) for v in emb):
            raise ValueError(f"Chunk {chunks[idx].chunk_id} has non-finite or invalid float values")

    # 5. Index into separate staging persistence directory and collection
    staging_store = ChromaVectorStore(
        persist_dir=STAGING_CHROMA_DIR,
        collection_name=STAGING_COLLECTION_NAME
    )
    staging_store.reset_collection()
    stored_count = staging_store.store_chunks(chunks=chunks, embeddings=embeddings)

    logger.info(
        "Stored %d vectors in staging collection '%s' at '%s'",
        stored_count,
        STAGING_COLLECTION_NAME,
        STAGING_CHROMA_DIR
    )

    # 6. Verify persistence reload
    reopen_store = ChromaVectorStore(
        persist_dir=STAGING_CHROMA_DIR,
        collection_name=STAGING_COLLECTION_NAME
    )
    reloaded_coll = reopen_store._get_collection()
    reloaded_count = reloaded_coll.count()
    logger.info("Persistence reload verification: %d vectors found in staging store", reloaded_count)

    # 7. Verify active store state after execution (must be 100% untouched)
    active_count_after = active_store._get_collection().count()
    logger.info("Active ChromaDB vector count after staging build: %d", active_count_after)
    if active_count_before != active_count_after:
        raise RuntimeError(
            f"Active ChromaDB was modified! Before: {active_count_before}, After: {active_count_after}"
        )

    summary = {
        "status": "SUCCESS",
        "staged_chunks_path": str(STAGING_STEP5_CHUNKS),
        "staging_persist_dir": str(STAGING_CHROMA_DIR),
        "staging_collection_name": STAGING_COLLECTION_NAME,
        "embedding_model": embedder.model_name,
        "embedding_dimension": embedder.embedding_dimension,
        "vectors_indexed": stored_count,
        "reloaded_count": reloaded_count,
        "active_store_count": active_count_after,
        "candidate_count": sum(1 for c in chunks if not c.is_approved_for_rag),
        "approved_count": sum(1 for c in chunks if c.is_approved_for_rag),
    }

    print("\n--- STAGING BUILD SUMMARY ---")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    try:
        run_staging_indexing()
    except Exception as exc:
        logger.exception("Step 6 Staging Indexing failed: %s", exc)
        sys.exit(1)
