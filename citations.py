"""Deterministic citation and provenance layer for ABC Shield regulatory RAG.

Extracts, validates, and formats citations and full audit provenance chains
strictly from retrieved evidence chunks. Operates entirely outside the LLM
to guarantee zero citation hallucination.

Citation scope:
- Implements "retrieved-evidence provenance", not sentence-level attribution.
- When an answer is grounded (is_grounded=True), citations and provenance are
  constructed deterministically from the retrieved evidence chunks supplied
  as the grounding context, subject to whitelist and deduplication rules.
- When is_grounded=False or status is INSUFFICIENT_EVIDENCE, no citations or
  provenance records are generated (citations = [], provenance = []).
- Never queries the LLM for citation IDs, URLs, or section numbers.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from pydantic import BaseModel, Field, field_validator
import logging

from rag.retrieval.retriever import RetrievalResult

logger = logging.getLogger(__name__)


class ProvenanceRecord(BaseModel):
    """Complete traceable lineage record for a regulatory evidence chunk."""

    record_id: str = Field(..., description="Parent Regulatory Record ID (e.g. RR-UK-01)")
    source_id: str = Field(..., description="Linked Source Register ID (e.g. UK-01)")
    regulation: str = Field(..., description="Regulation name")
    regulator: Optional[str] = Field(None, description="Issuing regulator or authority")
    jurisdiction: str = Field(..., description="Jurisdiction (UK, EU)")
    section_article: str = Field(..., description="Specific section or article reference")
    title: str = Field(..., description="Section / requirement title")
    official_source: Optional[str] = Field(None, description="Canonical official URL / link")
    version_date: Optional[str] = Field(None, description="Version or last updated timestamp")
    effective_date: Optional[str] = Field(None, description="Effective publication date")
    validation_status: str = Field(..., description="Validation status (e.g. Candidate - Awaiting Approval)")
    validation_date: Optional[str] = Field(None, description="Date of validation / review")
    is_approved_for_rag: bool = Field(False, description="Authoritative RAG approval flag")
    chunk_id: str = Field(..., description="Specific chunk identifier (e.g. RR-UK-01-C01)")
    text_type: str = Field(..., description="Type of evidence text (e.g. requirement_paraphrase)")
    similarity_score: Optional[float] = Field(None, description="Cosine similarity score from retrieval")

    @field_validator("chunk_id", "record_id", "source_id", "regulation", "section_article", "jurisdiction")
    @classmethod
    def validate_non_empty_provenance(cls, value: str, info: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            field_name = getattr(info, "field_name", "provenance")
            raise ValueError(f"Provenance field '{field_name}' cannot be empty or whitespace-only.")
        return value.strip()


class Citation(BaseModel):
    """Deterministic citation model referencing retrieved regulatory evidence."""

    citation_id: str = Field(..., description="Deterministic citation identifier (e.g. CIT-RR-UK-01-C01)")
    chunk_id: str = Field(..., description="Referenced chunk identifier")
    record_id: str = Field(..., description="Parent regulatory record identifier")
    source_id: str = Field(..., description="Parent source register identifier")
    regulation: str = Field(..., description="Official regulation title")
    regulator: Optional[str] = Field(None, description="Issuing authority or regulator")
    jurisdiction: str = Field(..., description="Jurisdiction (UK, EU)")
    section_article: str = Field(..., description="Section, article, or principle reference")
    title: str = Field(..., description="Requirement or section title")
    topic: Optional[str] = Field(None, description="Regulatory topic classification")
    official_source: Optional[str] = Field(None, description="Canonical official URL")
    version_date: Optional[str] = Field(None, description="Version or last updated timestamp")
    effective_date: Optional[str] = Field(None, description="Effective date")
    validation_status: str = Field(..., description="Validation status (e.g. Candidate - Awaiting Approval)")
    validation_date: Optional[str] = Field(None, description="Date of validation / review")
    is_approved_for_rag: bool = Field(False, description="Approval flag")
    text_type: str = Field(..., description="Evidence text type")
    formatted_citation: str = Field(
        ...,
        description="Human-readable citation string: [Chunk ID | Record ID | Regulation | Section]"
    )

    @field_validator("chunk_id", "record_id", "source_id", "regulation", "section_article", "jurisdiction")
    @classmethod
    def validate_non_empty_provenance(cls, value: str, info: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            field_name = getattr(info, "field_name", "provenance")
            raise ValueError(f"Provenance field '{field_name}' cannot be empty or whitespace-only.")
        return value.strip()

    @classmethod
    def from_retrieval_result(cls, chunk: RetrievalResult) -> "Citation":
        """Construct a Citation deterministically from a RetrievalResult object."""
        formatted = f"[{chunk.chunk_id} | {chunk.record_id} | {chunk.regulation} | {chunk.section_article}]"
        return cls(
            citation_id=f"CIT-{chunk.chunk_id}",
            chunk_id=chunk.chunk_id,
            record_id=chunk.record_id,
            source_id=chunk.source_id,
            regulation=chunk.regulation,
            regulator=chunk.regulator,
            jurisdiction=chunk.jurisdiction,
            section_article=chunk.section_article,
            title=chunk.title,
            topic=chunk.topic,
            official_source=chunk.official_source,
            version_date=chunk.version_date,
            effective_date=chunk.effective_date,
            validation_status=chunk.validation_status,
            validation_date=getattr(chunk, "validation_date", None),
            is_approved_for_rag=chunk.is_approved_for_rag,
            text_type=chunk.text_type,
            formatted_citation=formatted,
        )

    def to_provenance(self, similarity_score: Optional[float] = None) -> ProvenanceRecord:
        """Convert citation to complete provenance record."""
        return ProvenanceRecord(
            record_id=self.record_id,
            source_id=self.source_id,
            regulation=self.regulation,
            regulator=self.regulator,
            jurisdiction=self.jurisdiction,
            section_article=self.section_article,
            title=self.title,
            official_source=self.official_source,
            version_date=self.version_date,
            effective_date=self.effective_date,
            validation_status=self.validation_status,
            validation_date=self.validation_date,
            is_approved_for_rag=self.is_approved_for_rag,
            chunk_id=self.chunk_id,
            text_type=self.text_type,
            similarity_score=similarity_score,
        )


class CitationBuilder:
    """Deterministic builder and validator for citations and provenance records.

    Enforces retrieved-evidence provenance without relying on LLM attribution.
    """

    @staticmethod
    def is_valid_provenance(chunk: Any) -> bool:
        """Verify that an evidence chunk possesses complete, non-empty trusted provenance."""
        if not chunk:
            return False
        required_fields = ["chunk_id", "record_id", "source_id", "regulation", "section_article", "jurisdiction"]
        for field in required_fields:
            val = getattr(chunk, field, None)
            if not isinstance(val, str) or not val.strip():
                return False
        return True

    @staticmethod
    def build_citations(
        retrieved_chunks: List[RetrievalResult],
        is_grounded: bool = True,
    ) -> Tuple[List[Citation], List[ProvenanceRecord]]:
        """Construct validated citations and provenance records.

        Integrity Rules:
        1. If retrieved_chunks is empty or is_grounded is False -> return ([], []).
        2. A citation may ONLY reference a chunk where chunk.chunk_id in {c.chunk_id for c in retrieved_chunks}.
        3. Deterministically deduplicates citations preserving retrieval ranking order.
        4. Preserves all metadata from RetrievalResult exactly as provided, preserving nulls.

        Args:
            retrieved_chunks: List of RetrievalResult objects supplied as evidence.
            is_grounded: Whether the response was successfully grounded on supplied evidence.

        Returns:
            Tuple of (List[Citation], List[ProvenanceRecord]).
        """
        if not retrieved_chunks or not is_grounded:
            return [], []

        # 1. Build whitelist of valid retrieved chunk IDs
        retrieved_map: Dict[str, RetrievalResult] = {c.chunk_id: c for c in retrieved_chunks}
        valid_chunk_ids: Set[str] = set(retrieved_map.keys())

        citations: List[Citation] = []
        provenance: List[ProvenanceRecord] = []
        seen_chunk_ids: Set[str] = set()

        for chunk in retrieved_chunks:
            cid = chunk.chunk_id

            # Whitelist verification: strictly reject any chunk not in retrieved set
            if cid not in valid_chunk_ids:
                continue

            # Provenance integrity verification (RAG-04 / RAG-13)
            if not CitationBuilder.is_valid_provenance(chunk):
                logger.warning("Rejecting chunk '%s' due to missing or untrusted provenance.", cid)
                continue

            # Deterministic deduplication
            if cid in seen_chunk_ids:
                continue
            seen_chunk_ids.add(cid)

            # Construct citation and provenance deterministically from metadata
            citation = Citation.from_retrieval_result(chunk)
            prov = citation.to_provenance(similarity_score=chunk.similarity_score)

            citations.append(citation)
            provenance.append(prov)

        return citations, provenance
