"""Retrieval interface for ABC Shield regulatory chunks.

Retrieves grounded evidence chunks with full provenance and metadata.
Does NOT generate final LLM answers — returns evidence only.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from rag.retrieval.embeddings import EmbeddingManager
from rag.retrieval.vector_store import ChromaVectorStore


class RetrievalResult(BaseModel):
    """Structured evidence chunk retrieved from the vector store."""
    chunk_id: str = Field(..., description="Unique chunk ID")
    record_id: str = Field(..., description="Parent regulatory record ID")
    source_id: str = Field(..., description="Parent source ID")
    regulation: str = Field(..., description="Regulation name")
    regulator: str = Field(..., description="Issuing regulator/authority")
    jurisdiction: str = Field(..., description="Jurisdiction (e.g. UK, EU)")
    section_article: str = Field(..., description="Section or article reference")
    title: str = Field(..., description="Section / requirement title")
    text: str = Field(..., description="Evidence text content")
    text_type: str = Field(..., description="e.g. 'requirement_paraphrase'")
    topic: Optional[str] = Field(None, description="Topic taxonomy")
    official_source: Optional[str] = Field(None, description="Canonical official URL")
    version_date: Optional[str] = Field(None, description="Version or last updated timestamp")
    effective_date: Optional[str] = Field(None, description="Effective date")
    validation_status: str = Field(..., description="Validation status (e.g. Candidate - Awaiting Approval)")
    validation_date: Optional[str] = Field(None, description="Date of validation / review")
    is_approved_for_rag: bool = Field(False, description="Whether record is approved authoritative evidence")
    authority_level: Optional[str] = Field(None, description="Authority level (A, B, C, D)")
    source_type: Optional[str] = Field(None, description="Source classification")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    distance: float = Field(..., description="Cosine distance metric")
    project_id: Optional[str] = Field(None, description="Project or tenant identifier")


class RegulatoryRetriever:
    """Retrieves relevant regulatory chunks based on query embeddings and metadata filters."""

    def __init__(
        self,
        embedding_manager: Optional[EmbeddingManager] = None,
        vector_store: Optional[ChromaVectorStore] = None,
    ):
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.vector_store = vector_store or ChromaVectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_approved_only: bool = False,
        jurisdiction: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """Retrieve the most relevant regulatory chunks for a query.

        Args:
            query: User or compliance query string.
            top_k: Maximum number of chunks to return (clamped between 1 and 20).
            filter_approved_only: If True, only returns chunks where is_approved_for_rag == True.
            jurisdiction: Optional jurisdiction filter (e.g. "UK" or "EU").
            project_id: Optional project or tenant filter for multi-tenant isolation.

        Returns:
            List of RetrievalResult objects representing retrieved evidence.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        # Bound maximum query length to prevent embedding memory exhaustion (RAG-09)
        if len(clean_query) > 5000:
            clean_query = clean_query[:5000]

        # Clamp top_k to safe bounds (1 to 20) to prevent context exhaustion and bulk extraction
        try:
            safe_top_k = max(1, min(int(top_k), 20))
        except (ValueError, TypeError):
            safe_top_k = 5

        # 1. Generate query embedding
        query_embedding = self.embedding_manager.embed_text(clean_query)

        # 2. Build metadata filter conditions
        where_clauses = []
        if filter_approved_only:
            where_clauses.append({"is_approved_for_rag": True})
        if jurisdiction and jurisdiction.strip():
            jur_req = jurisdiction.strip()
            if jur_req.upper() in ("EU", "EU-LEVEL"):
                where_clauses.append({"jurisdiction": {"$in": ["EU", "EU-level"]}})
            elif jur_req.upper() in ("UK", "UNITED KINGDOM"):
                where_clauses.append({"jurisdiction": {"$in": ["UK", "United Kingdom"]}})
            else:
                where_clauses.append({"jurisdiction": jur_req})
        if project_id and project_id.strip():
            where_clauses.append({"project_id": project_id.strip()})

        where_filter = None
        if len(where_clauses) == 1:
            where_filter = where_clauses[0]
        elif len(where_clauses) > 1:
            where_filter = {"$and": where_clauses}

        # 3. Query vector store with candidate pool
        pool_k = max(safe_top_k * 4, 25)
        raw_results = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=pool_k,
            where=where_filter,
        )

        # 4. Map raw results to typed RetrievalResult objects
        results: List[RetrievalResult] = []
        for r in raw_results:
            meta = r.get("metadata", {})
            res = RetrievalResult(
                chunk_id=r["chunk_id"],
                record_id=meta.get("record_id", ""),
                source_id=meta.get("source_id", ""),
                regulation=meta.get("regulation", ""),
                regulator=meta.get("regulator", ""),
                jurisdiction=meta.get("jurisdiction", ""),
                section_article=meta.get("section_article", ""),
                title=meta.get("title", ""),
                text=r["text"],
                text_type=meta.get("text_type", "requirement_paraphrase"),
                topic=meta.get("topic") or None,
                official_source=meta.get("official_source") or None,
                version_date=meta.get("version_date") or None,
                effective_date=meta.get("effective_date") or None,
                validation_status=meta.get("validation_status", "Candidate - Awaiting Approval"),
                validation_date=meta.get("validation_date") or None,
                is_approved_for_rag=bool(meta.get("is_approved_for_rag", False)),
                authority_level=meta.get("authority_level") or None,
                source_type=meta.get("source_type") or None,
                similarity_score=r.get("similarity_score", 0.0),
                distance=r.get("distance", 0.0),
                project_id=meta.get("project_id") or None,
            )
            results.append(res)

        # 5. Defense-in-depth post-retrieval validation
        if filter_approved_only:
            results = [r for r in results if r.is_approved_for_rag is True]
        if jurisdiction and jurisdiction.strip():
            jur_req = jurisdiction.strip().upper()
            if jur_req in ("EU", "EU-LEVEL"):
                results = [r for r in results if r.jurisdiction.upper() in ("EU", "EU-LEVEL")]
            elif jur_req in ("UK", "UNITED KINGDOM"):
                results = [r for r in results if r.jurisdiction.upper() in ("UK", "UNITED KINGDOM")]
            else:
                results = [r for r in results if r.jurisdiction.lower() == jurisdiction.strip().lower()]
        if project_id and project_id.strip():
            results = [r for r in results if r.project_id == project_id.strip()]

        return self._rerank_candidates(clean_query, results, top_k=safe_top_k)

    @staticmethod
    def _rerank_candidates(query: str, candidates: List[RetrievalResult], top_k: int = 5) -> List[RetrievalResult]:
        """Re-rank candidate evidence chunks based on exact regulatory provision matches and query intent.

        Preserves original similarity_score and distance on the returned RetrievalResult objects.
        """
        if not candidates:
            return []

        import re
        query_lower = query.lower()

        # 1. Detect explicit provision references
        sec_matches = set(re.findall(r"\bsection\s+(\d+|[a-zA-Z0-9]+)\b", query_lower))
        art_matches = set(re.findall(r"\barticle\s+(\d+|[a-zA-Z0-9]+)\b", query_lower))
        fcg_matches = set(re.findall(r"\b(fcg\s*\d+(?:\.\d+)*)\b", query_lower))

        # Linked topics
        if "associated person" in query_lower:
            sec_matches.add("8")
        if "failure to prevent" in query_lower or "corporate failure" in query_lower:
            sec_matches.add("7")
        if "bribing another person" in query_lower:
            sec_matches.add("1")
        if "being bribed" in query_lower:
            sec_matches.add("2")

        # Section 7 linkage to Section 8 definition
        if "7" in sec_matches:
            sec_matches.add("8")

        has_provision_query = bool(sec_matches or art_matches or fcg_matches)
        if not has_provision_query:
            return candidates[:top_k]

        scored = []
        for c in candidates:
            rank_score = c.similarity_score
            c_sec = (c.section_article or "").lower()
            c_title = (c.title or "").lower()

            # Section matching
            for s_num in sec_matches:
                if f"section {s_num}" in c_sec or f"section {s_num}" in c_title:
                    if "associated person" in query_lower and s_num == "8":
                        rank_score += 3.0
                    elif "section 7" in query_lower and s_num == "7":
                        rank_score += 3.0
                    elif "section 7" in query_lower and s_num == "8":
                        rank_score += 2.5
                    elif "section 2" in query_lower and s_num == "2":
                        rank_score += 3.0
                    else:
                        rank_score += 2.0

            # Article matching
            for a_num in art_matches:
                if f"article {a_num}" in c_sec or f"article {a_num}" in c_title:
                    rank_score += 2.5

            # FCG matching
            for fcg in fcg_matches:
                fcg_norm = re.sub(r"\s+", " ", fcg.strip())
                if fcg_norm in re.sub(r"\s+", " ", c_sec) or fcg_norm in re.sub(r"\s+", " ", c_title):
                    rank_score += 3.0
                elif "fcg 6.2.3" in fcg_norm and "fcg 6.2.4" in c_sec:
                    rank_score -= 2.0
                elif "fcg 6.2.4" in fcg_norm and "fcg 6.2.3" in c_sec:
                    rank_score -= 2.0

            scored.append((rank_score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]


class StagedRegulatoryRetriever(RegulatoryRetriever):
    """Isolated retriever pointing strictly to the staged ChromaDB canonical 25-vector collection.

    Guarantees that staging queries target the staged database and fail closed
    if the staged store is missing, preventing silent fallback to the active production index.
    """

    DEFAULT_STAGING_PERSIST_DIR = Path("data/staging/madhesh_handover/step6/chroma_db")
    DEFAULT_STAGING_COLLECTION_NAME = "canonical_regulatory_records"

    def __init__(
        self,
        persist_dir: Path = DEFAULT_STAGING_PERSIST_DIR,
        collection_name: str = DEFAULT_STAGING_COLLECTION_NAME,
        embedding_manager: Optional[EmbeddingManager] = None,
    ):
        path = Path(persist_dir)
        if not path.exists():
            raise FileNotFoundError(
                f"Staging ChromaDB directory not found: {path}. "
                "Failing closed to prevent silent fallback to production ChromaDB."
            )
        staged_store = ChromaVectorStore(persist_dir=path, collection_name=collection_name)
        super().__init__(
            embedding_manager=embedding_manager,
            vector_store=staged_store,
        )

