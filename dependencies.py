"""Dependency injection and shared RAG component wiring for FastAPI backend.

Guarantees that EmbeddingManager, ChromaVectorStore, RegulatoryRetriever, and
GroundedGenerator are initialized once and reused across HTTP requests rather than
recreated on each call.
"""

from pathlib import Path
from typing import Optional
import logging

from rag.generation.grounded_generator import GroundedGenerator
from rag.retrieval.retriever import RegulatoryRetriever
from rag.retrieval.vector_store import ChromaVectorStore
from rag.retrieval.embeddings import EmbeddingManager
from rag.conflict.conflict_detector import ConflictDetector
from config.settings import settings

logger = logging.getLogger(__name__)

_grounded_generator_instance: Optional[GroundedGenerator] = None


def get_configured_vector_store() -> ChromaVectorStore:
    """Retrieve or initialize the ChromaVectorStore configured for the application.

    Supports 'canonical' (default, pointing to staged 25-vector canonical store)
    and 'legacy' (pointing to original 15-vector production store).
    Fails closed if the configured canonical persist directory does not exist,
    preventing silent fallback to the legacy production index.
    """
    mode = getattr(settings, "rag_knowledge_base_mode", "canonical").strip().lower()

    if mode == "canonical":
        persist_dir = Path(getattr(settings, "canonical_chroma_persist_dir", "data/staging/madhesh_handover/step6/chroma_db"))
        collection_name = getattr(settings, "canonical_chroma_collection_name", "canonical_regulatory_records")
        if not persist_dir.exists():
            raise FileNotFoundError(
                f"Canonical ChromaDB persist directory '{persist_dir}' does not exist. "
                "Failing closed to prevent silent fallback to legacy production store."
            )
        return ChromaVectorStore(persist_dir=persist_dir, collection_name=collection_name)
    elif mode == "legacy":
        persist_dir = Path(getattr(settings, "legacy_chroma_persist_dir", "data/processed/chroma_db"))
        collection_name = getattr(settings, "legacy_chroma_collection_name", "regulatory_records")
        if not persist_dir.exists():
            raise FileNotFoundError(
                f"Legacy ChromaDB persist directory '{persist_dir}' does not exist."
            )
        return ChromaVectorStore(persist_dir=persist_dir, collection_name=collection_name)
    else:
        persist_dir = Path(settings.chroma_persist_dir)
        collection_name = settings.chroma_collection_name
        if not persist_dir.exists():
            raise FileNotFoundError(
                f"Configured ChromaDB persist directory '{persist_dir}' does not exist."
            )
        return ChromaVectorStore(persist_dir=persist_dir, collection_name=collection_name)


def get_grounded_generator() -> GroundedGenerator:
    """Retrieve or initialize the shared singleton GroundedGenerator instance.

    Reuses singletons for ChromaVectorStore, EmbeddingManager, and ConflictDetector.
    """
    global _grounded_generator_instance
    if _grounded_generator_instance is None:
        logger.info("Initializing shared GroundedGenerator and RAG components...")
        embedding_mgr = EmbeddingManager()
        vector_store = get_configured_vector_store()
        retriever = RegulatoryRetriever(
            embedding_manager=embedding_mgr,
            vector_store=vector_store,
        )
        conflict_detector = ConflictDetector()
        _grounded_generator_instance = GroundedGenerator(
            retriever=retriever,
            conflict_detector=conflict_detector,
        )
        logger.info(
            "Shared GroundedGenerator initialized successfully with collection '%s' at '%s'.",
            vector_store.collection_name,
            vector_store.persist_dir,
        )
    return _grounded_generator_instance


def reset_grounded_generator() -> None:
    """Reset the shared GroundedGenerator instance for cache busting or re-configuration."""
    global _grounded_generator_instance
    _grounded_generator_instance = None


def check_chromadb_connectivity() -> bool:
    """Non-sensitive check verifying ChromaDB is responsive."""
    try:
        gen = get_grounded_generator()
        count = gen.retriever.vector_store._get_collection().count()
        return count >= 0
    except Exception as e:
        logger.error("ChromaDB connectivity check failed: %s", e)
        return False


def get_advice_adapter() -> "AdviceRAGAdapter":
    """Retrieve or initialize an AdviceRAGAdapter wired to the shared GroundedGenerator."""
    from rag.pipeline.advice_adapter import AdviceRAGAdapter
    return AdviceRAGAdapter(generator=get_grounded_generator())


def get_advice_comparator() -> "AdviceComparator":
    """Retrieve or initialize an AdviceComparator wired to the shared retriever and conflict detector."""
    from rag.pipeline.advice_comparator import AdviceComparator
    gen = get_grounded_generator()
    return AdviceComparator(retriever=gen.retriever, conflict_detector=gen.conflict_detector)


