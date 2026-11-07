"""Reproducible seeding script for ABC Shield Canonical ChromaDB vector store.

Loads canonical 25-record corpus from staging, generates embeddings using
all-MiniLM-L6-v2 on CPU, and indexes into the persistent collection
`canonical_regulatory_records` under data/staging/madhesh_handover/step6/chroma_db/.

Ensures deterministic execution, zero duplicates on repeat runs, and strict
preservation of all regulatory provenance metadata.
"""

from pathlib import Path
import json
import logging
import math
import sys

# Deterministically resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CANONICAL_CHUNKS_PATH = PROJECT_ROOT / "data" / "staging" / "fast_track" / "regulatory_chunks.json"
FALLBACK_CHUNKS_PATH = PROJECT_ROOT / "data" / "staging" / "madhesh_handover" / "step5" / "regulatory_chunks.json"
TARGET_PERSIST_DIR = PROJECT_ROOT / "data" / "staging" / "madhesh_handover" / "step6" / "chroma_db"
COLLECTION_NAME = "canonical_regulatory_records"
EXPECTED_COUNT = 25
MODEL_NAME = "all-MiniLM-L6-v2"
EXPECTED_DIM = 384


def seed_canonical_vectors(reset: bool = False) -> dict:
    """Seed or update canonical regulatory vector collection deterministically."""
    logger.info("=== Seeding Canonical Regulatory Vectors ===")
    logger.info("Project Root: %s", PROJECT_ROOT)
    logger.info("Target Persist Dir: %s", TARGET_PERSIST_DIR)
    logger.info("Collection Name: %s", COLLECTION_NAME)

    # 1. Locate canonical dataset
    if CANONICAL_CHUNKS_PATH.exists():
        chunks_source = CANONICAL_CHUNKS_PATH
    elif FALLBACK_CHUNKS_PATH.exists():
        chunks_source = FALLBACK_CHUNKS_PATH
    else:
        raise FileNotFoundError(
            f"Canonical source dataset not found at {CANONICAL_CHUNKS_PATH} or {FALLBACK_CHUNKS_PATH}. "
            "Cannot fabricate regulatory records."
        )

    logger.info("Loading canonical dataset from %s", chunks_source)
    with open(chunks_source, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    if len(raw_items) != EXPECTED_COUNT:
        raise ValueError(f"Expected exactly {EXPECTED_COUNT} canonical chunks, found {len(raw_items)}")

    # Ensure Option A governance in memory if loaded from unadapted fallback
    chunks = []
    for item in raw_items:
        chunk = RegulatoryChunk(**item)
        # Verify regulatory integrity invariants
        assert chunk.is_approved_for_rag is False, f"Chunk {chunk.chunk_id} must have is_approved_for_rag=False"
        assert chunk.validation_status == "Approved for RAG Integration - Pending SME Validation", (
            f"Chunk {chunk.chunk_id} validation_status must be 'Approved for RAG Integration - Pending SME Validation', "
            f"found '{chunk.validation_status}'"
        )
        chunks.append(chunk)

    logger.info("Loaded %d validated canonical chunks.", len(chunks))

    # 2. Initialize embedding manager and embed
    embedder = EmbeddingManager(model_name=MODEL_NAME)
    texts = [c.text for c in chunks]
    embeddings = embedder.embed_texts(texts)

    logger.info(
        "Generated %d embeddings with '%s' (dimension: %d)",
        len(embeddings),
        embedder.model_name,
        embedder.embedding_dimension,
    )

    if embedder.embedding_dimension != EXPECTED_DIM:
        raise ValueError(
            f"Expected embedding dimension {EXPECTED_DIM}, got {embedder.embedding_dimension}"
        )

    for idx, emb in enumerate(embeddings):
        if len(emb) != EXPECTED_DIM or not all(isinstance(v, float) and math.isfinite(v) for v in emb):
            raise ValueError(f"Invalid embedding vector generated for chunk {chunks[idx].chunk_id}")

    # 3. Store into ChromaDB
    TARGET_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    store = ChromaVectorStore(persist_dir=TARGET_PERSIST_DIR, collection_name=COLLECTION_NAME)

    if reset:
        store.reset_collection()

    stored_count = store.store_chunks(chunks=chunks, embeddings=embeddings)

    # 4. Reload and verify vector count and collection name
    reloaded_store = ChromaVectorStore(persist_dir=TARGET_PERSIST_DIR, collection_name=COLLECTION_NAME)
    reloaded_col = reloaded_store._get_collection()
    final_count = reloaded_col.count()

    logger.info("Canonical vector store ready. Final vector count: %d in '%s'", final_count, COLLECTION_NAME)

    if final_count != EXPECTED_COUNT:
        raise RuntimeError(f"Expected {EXPECTED_COUNT} vectors in '{COLLECTION_NAME}', found {final_count}")

    # Verification sample
    sample = reloaded_col.get(limit=1, include=["metadatas"])
    sample_meta = sample["metadatas"][0] if sample["metadatas"] else {}
    logger.info(
        "Sample record: ID=%s, validation_status='%s', is_approved_for_rag=%s",
        sample["ids"][0],
        sample_meta.get("validation_status"),
        sample_meta.get("is_approved_for_rag"),
    )

    result = {
        "status": "SUCCESS",
        "collection_name": COLLECTION_NAME,
        "persist_dir": str(TARGET_PERSIST_DIR),
        "embedding_model": MODEL_NAME,
        "embedding_dimension": EXPECTED_DIM,
        "vector_count": final_count,
        "source_dataset": str(chunks_source),
    }
    print(f"\nFinal Vector Count: {final_count}")
    print(f"Collection Name: {COLLECTION_NAME}")
    return result


if __name__ == "__main__":
    seed_canonical_vectors()
