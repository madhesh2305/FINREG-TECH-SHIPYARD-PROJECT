"""Persistent ChromaDB vector store manager for regulatory chunks.

Maintains strict provenance metadata and validation-status gating.
Uses local persistence under data/processed/chroma_db/.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from rag.ingestion.schemas import RegulatoryChunk

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Manages persistent ChromaDB vector storage for ABC Shield regulatory chunks."""

    DEFAULT_PERSIST_DIR = Path("data/processed/chroma_db")
    DEFAULT_COLLECTION_NAME = "regulatory_records"

    def __init__(
        self,
        persist_dir: Path = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None

    def _get_client(self):
        """Lazy initialization of ChromaDB PersistentClient."""
        if self._client is None:
            try:
                import chromadb
                self._client = chromadb.PersistentClient(path=str(self.persist_dir))
            except ImportError as e:
                raise ImportError(
                    "chromadb is not installed. Please install with `pip install chromadb`."
                ) from e
        return self._client

    def _get_collection(self):
        """Retrieve or create the regulatory records collection with cosine distance."""
        if self._collection is None:
            client = self._get_client()
            # Use cosine distance for normalized embeddings
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def reset_collection(self) -> None:
        """Safely delete and recreate the collection with cosine distance metadata."""
        client = self._get_client()
        try:
            client.delete_collection(name=self.collection_name)
            logger.info("Deleted existing collection '%s'", self.collection_name)
        except Exception as e:
            logger.info("Collection '%s' did not exist or could not be deleted: %s", self.collection_name, e)

        self._collection = client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Created clean collection '%s' with cosine distance", self.collection_name)

    @staticmethod
    def _sanitize_metadata(chunk: RegulatoryChunk) -> Dict[str, Any]:
        """Convert chunk attributes into ChromaDB-compatible scalar metadata.

        ChromaDB supports str, int, float, bool. Nulls are converted to empty strings.
        Includes all Week 4 enriched regulatory fields.
        """
        return {
            "chunk_id": str(chunk.chunk_id),
            "record_id": str(chunk.record_id),
            "source_id": str(chunk.source_id),
            "regulation": str(chunk.regulation or ""),
            "regulator": str(chunk.regulator or ""),
            "jurisdiction": str(chunk.jurisdiction or ""),
            "section_article": str(chunk.section_article or ""),
            "title": str(chunk.title or ""),
            "topic": str(chunk.topic or ""),
            "official_source": str(chunk.official_source or ""),
            "version_date": str(chunk.version_date or ""),
            "effective_date": str(chunk.effective_date or ""),
            "validation_status": str(chunk.validation_status or ""),
            "validation_date": str(chunk.validation_date or ""),
            "is_approved_for_rag": bool(chunk.is_approved_for_rag),
            "text_type": str(chunk.text_type or "retrieval_text"),
            "authority_level": str(chunk.authority_level or ""),
            "source_type": str(chunk.source_type or ""),
            "chunk_index": int(chunk.chunk_index),
            "total_chunks": int(chunk.total_chunks),
            # Week 4 Enriched Metadata fields
            "content_type": str(chunk.content_type or ""),
            "retrieval_tags": "; ".join(chunk.retrieval_tags) if chunk.retrieval_tags else "",
            "citation_label": str(chunk.citation_label or ""),
            "retrieval_priority": str(chunk.retrieval_priority or ""),
            "authority_rule": str(chunk.authority_rule or ""),
            "rag_instruction": str(chunk.rag_instruction or ""),
            "official_source_check_note": str(chunk.official_source_check_note or ""),
        }

    def store_chunks(
        self,
        chunks: List[RegulatoryChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Store or update regulatory chunks and their embeddings in ChromaDB.

        Args:
            chunks: List of RegulatoryChunk models.
            embeddings: Corresponding embedding vectors.

        Returns:
            Number of documents stored.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Count mismatch: received {len(chunks)} chunks and {len(embeddings)} embeddings."
            )

        if not chunks:
            return 0

        collection = self._get_collection()

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [self._sanitize_metadata(c) for c in chunks]

        # Use upsert so repeated runs are idempotent
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            "Successfully stored %d chunks in ChromaDB collection '%s'",
            len(chunks),
            self.collection_name
        )
        return len(chunks)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return operational statistics for the vector collection."""
        collection = self._get_collection()
        return {
            "collection_name": self.collection_name,
            "persist_directory": str(self.persist_dir),
            "total_vectors": collection.count(),
        }

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the vector store with an embedding vector and optional metadata filters."""
        collection = self._get_collection()

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)

        formatted_results = []
        if not results or not results["ids"] or not results["ids"][0]:
            return formatted_results

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            # For cosine distance, distance = 1 - cosine_similarity (range 0 to 2)
            # Similarity score = 1 - distance (normalized 0 to 1 for positive similarities)
            similarity = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
            formatted_results.append({
                "chunk_id": chunk_id,
                "text": doc,
                "metadata": meta,
                "distance": dist,
                "similarity_score": round(similarity, 4),
            })

        return formatted_results
