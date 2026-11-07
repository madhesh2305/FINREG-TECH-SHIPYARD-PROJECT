"""Retrieval package for ABC Shield / FinRegTech ShipYard.

Exposes embeddings manager, ChromaDB vector store, retriever, and chunk indexing pipeline.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

from rag.ingestion.schemas import RegulatoryChunk
from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult, StagedRegulatoryRetriever

logger = logging.getLogger(__name__)


def index_processed_chunks(
    chunks_path: Path = Path("data/processed/regulatory_chunks.json"),
    persist_dir: Path = Path("data/processed/chroma_db"),
    collection_name: str = "regulatory_records",
    embedding_model_name: str = EmbeddingManager.DEFAULT_MODEL_NAME,
    reset_collection: bool = True,
) -> Dict[str, Any]:
    """Load processed regulatory chunks, generate embeddings, and index into ChromaDB.

    Args:
        chunks_path: Path to regulatory_chunks.json generated in W4.5.
        persist_dir: Target directory for ChromaDB local persistence.
        collection_name: ChromaDB collection name.
        embedding_model_name: Sentence-transformers model name.
        reset_collection: If True, deletes and recreates the collection before indexing.

    Returns:
        Summary dict containing counts and collection statistics.
    """
    path = Path(chunks_path)
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found at: {path}")

    # 1. Load chunks from processed JSON
    with open(path, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)

    chunks = [RegulatoryChunk(**c) for c in raw_chunks]
    logger.info("Loaded %d chunks from %s", len(chunks), path)

    # 2. Generate embeddings
    embedder = EmbeddingManager(model_name=embedding_model_name)
    texts = [c.text for c in chunks]
    embeddings = embedder.embed_texts(texts)

    # 3. Store in persistent ChromaDB
    store = ChromaVectorStore(persist_dir=persist_dir, collection_name=collection_name)
    if reset_collection:
        store.reset_collection()
    stored_count = store.store_chunks(chunks=chunks, embeddings=embeddings)

    stats = store.get_collection_stats()
    return {
        "status": "INDEXED",
        "chunks_loaded": len(chunks),
        "embeddings_generated": len(embeddings),
        "embedding_model": embedding_model_name,
        "embedding_dimension": embedder.embedding_dimension,
        "vectors_stored": stored_count,
        "collection_name": collection_name,
        "persist_directory": str(persist_dir),
        "collection_stats": stats,
    }


__all__ = [
    "EmbeddingManager",
    "ChromaVectorStore",
    "RegulatoryRetriever",
    "StagedRegulatoryRetriever",
    "RetrievalResult",
    "index_processed_chunks",
]
