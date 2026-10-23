"""Structured AI output models for ABC Shield / FinRegTech ShipYard.

Defines the stable, machine-readable output contract (StructuredAIResponse)
unifying retrieved evidence (Task 4), grounded generation (Task 5),
citations and provenance (Task 6), GAP analysis (Task 7), and conflict findings (Task 8).
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from rag.generation.citations import Citation, ProvenanceRecord
from rag.generation.gap_handler import GapResult
from rag.conflict.conflict_detector import ConflictFinding
from rag.retrieval.retriever import RetrievalResult


class ResponseStatus(str, Enum):
    """High-level lifecycle status of the structured AI response."""

    GROUNDED = "GROUNDED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNAPPROVED_EVIDENCE = "UNAPPROVED_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    ERROR = "ERROR"


class RetrievedEvidenceItem(BaseModel):
    """Structured representation of a retrieved regulatory evidence chunk for API/frontend consumption."""

    chunk_id: str = Field(..., description="Unique chunk identifier (e.g. RR-UK-01-C01)")
    record_id: str = Field(..., description="Parent regulatory record ID (e.g. RR-UK-01)")
    source_id: str = Field(..., description="Parent source register ID (e.g. UK-01)")
    regulation: str = Field(..., description="Regulation name")
    section_article: str = Field(..., description="Section or article reference")
    title: str = Field(..., description="Section or requirement title")
    text: str = Field(..., description="Actual evidence text content from retrieved chunk")
    similarity_score: Optional[float] = Field(None, description="Cosine similarity score from retrieval")
    similarity: Optional[float] = Field(None, description="Convenience alias for similarity_score")
    distance: Optional[float] = Field(None, description="Cosine distance metric from vector store")
    validation_status: str = Field(..., description="Validation status (e.g. Candidate - Awaiting Approval)")
    is_approved_for_rag: bool = Field(False, description="Whether approved for authoritative RAG use")
    official_source: Optional[str] = Field(None, description="Canonical official URL / reference")
    version_date: Optional[str] = Field(None, description="Version or last updated timestamp")
    effective_date: Optional[str] = Field(None, description="Publication or effective date")

    @classmethod
    def from_retrieval_result(cls, chunk: RetrievalResult) -> "RetrievedEvidenceItem":
        """Convert a RetrievalResult into a RetrievedEvidenceItem preserving exact values."""
        sim = getattr(chunk, "similarity_score", None)
        dist = getattr(chunk, "distance", None)
        return cls(
            chunk_id=chunk.chunk_id,
            record_id=chunk.record_id,
            source_id=chunk.source_id,
            regulation=chunk.regulation,
            section_article=chunk.section_article,
            title=chunk.title,
            text=chunk.text,
            similarity_score=sim,
            similarity=sim,
            distance=dist,
            validation_status=chunk.validation_status,
            is_approved_for_rag=chunk.is_approved_for_rag,
            official_source=chunk.official_source,
            version_date=chunk.version_date,
            effective_date=chunk.effective_date,
        )


class ResponseMetadata(BaseModel):
    """Deterministic operational metadata accompanying the structured AI response."""

    retrieved_count: int = Field(0, description="Total count of retrieved evidence chunks")
    approved_evidence_count: int = Field(0, description="Count of retrieved chunks approved for authoritative RAG")
    citation_count: int = Field(0, description="Count of citations generated")
    conflict_count: int = Field(0, description="Count of conflict/overlap findings identified")
    has_gap: bool = Field(False, description="Whether an evidence gap was identified by Task 7")
    gap_type: Optional[str] = Field(None, description="Taxonomy classification of the gap if present")
    requires_human_review: bool = Field(False, description="Whether compliance SME review is required")
    has_candidate_evidence: bool = Field(False, description="Whether unapproved candidate evidence was retrieved")
    response_version: str = Field("1.0", description="Contract schema version")


class StructuredAIResponse(BaseModel):
    """Unified machine-readable AI output contract for ABC Shield / FinRegTech ShipYard."""

    request_id: Optional[str] = Field(None, description="Optional request identifier for tracing")
    query: str = Field(..., description="Original user or compliance query")
    status: ResponseStatus = Field(..., description="Deterministic response lifecycle status")
    answer: Optional[str] = Field(None, description="Grounded answer text generated from supplied evidence")
    grounded: bool = Field(..., description="Whether the answer was successfully grounded on supplied evidence")
    gap: Optional[GapResult] = Field(None, description="Deterministic GAP analysis from Task 7 (null when grounded)")
    citations: List[Citation] = Field(default_factory=list, description="Deterministic citations from Task 6")
    provenance: List[ProvenanceRecord] = Field(default_factory=list, description="Traceable provenance chains from Task 6")
    conflicts: List[ConflictFinding] = Field(default_factory=list, description="Deterministic conflict/overlap findings from Task 8")
    retrieved_evidence: List[RetrievedEvidenceItem] = Field(default_factory=list, description="Structured evidence chunks retrieved from Task 4")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="Operational metadata and counts")

    def to_external_status(self) -> str:
        """Map internal lifecycle status to the W4.11 external product status string."""
        from rag.output.response_builder import StructuredResponseBuilder
        return StructuredResponseBuilder.map_external_status(self)
