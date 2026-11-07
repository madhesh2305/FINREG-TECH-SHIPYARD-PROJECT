"""Response builder for assembling StructuredAIResponse from pipeline outputs.

Performs deterministic assembly of existing Task 4–8 components without
performing independent reasoning, LLM generation, or gap re-classification.
"""

from typing import List, Optional
import logging

from rag.generation.grounded_generator import GroundedResponse
from rag.generation.gap_handler import GapType
from rag.retrieval.retriever import RetrievalResult
from rag.output.structured_response import (
    ResponseStatus,
    RetrievedEvidenceItem,
    ResponseMetadata,
    StructuredAIResponse,
)

logger = logging.getLogger(__name__)


class StructuredResponseBuilder:
    """Deterministic assembler for the unified StructuredAIResponse contract."""

    @classmethod
    def map_status(cls, grounded_response: GroundedResponse, error: Optional[str] = None) -> ResponseStatus:
        """Map existing GroundedResponse state and Task 7 GapType to ResponseStatus.

        Task 7 remains the sole authority for gap classification. Task 9 only
        performs deterministic enum mapping.
        """
        if error is not None:
            return ResponseStatus.ERROR

        if grounded_response.gap is not None and grounded_response.gap.is_gap:
            gap_type = grounded_response.gap.gap_type
            if gap_type == GapType.OUT_OF_SCOPE:
                return ResponseStatus.OUT_OF_SCOPE
            elif gap_type == GapType.UNAPPROVED_EVIDENCE:
                return ResponseStatus.UNAPPROVED_EVIDENCE
            elif gap_type == GapType.CONFLICTING_EVIDENCE:
                return ResponseStatus.CONFLICTING_EVIDENCE
            elif gap_type == GapType.NEEDS_HUMAN_REVIEW:
                return ResponseStatus.NEEDS_HUMAN_REVIEW
            else:
                return ResponseStatus.INSUFFICIENT_EVIDENCE

        if grounded_response.grounded:
            return ResponseStatus.GROUNDED

        return ResponseStatus.INSUFFICIENT_EVIDENCE

    @classmethod
    def build(
        cls,
        grounded_response: GroundedResponse,
        retrieved_chunks: Optional[List[RetrievalResult]] = None,
        request_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> StructuredAIResponse:
        """Assemble a StructuredAIResponse from existing pipeline outputs.

        Args:
            grounded_response: The GroundedResponse produced by GroundedGenerator.
            retrieved_chunks: The exact RetrievalResult objects returned by RegulatoryRetriever.
            request_id: Optional request identifier for tracing.
            error: Optional error description indicating pipeline failure.

        Returns:
            StructuredAIResponse instance conforming to the Task 9 contract.
        """
        from rag.generation.citations import CitationBuilder
        chunks = [c for c in (retrieved_chunks or []) if CitationBuilder.is_valid_provenance(c)]
        evidence_items = [RetrievedEvidenceItem.from_retrieval_result(c) for c in chunks]

        status = cls.map_status(grounded_response, error=error)

        approved_count = sum(1 for item in evidence_items if item.is_approved_for_rag)
        candidate_count = sum(1 for item in evidence_items if not item.is_approved_for_rag)
        has_gap = grounded_response.gap is not None and grounded_response.gap.is_gap
        gap_type_str = grounded_response.gap.gap_type.value if has_gap else None

        requires_human_review = False
        if has_gap and getattr(grounded_response.gap, "requires_human_review", False):
            requires_human_review = True
        elif len(grounded_response.conflicts) > 0:
            requires_human_review = True

        metadata = ResponseMetadata(
            retrieved_count=len(evidence_items),
            approved_evidence_count=approved_count,
            citation_count=len(grounded_response.citations),
            conflict_count=len(grounded_response.conflicts),
            has_gap=has_gap,
            gap_type=gap_type_str,
            requires_human_review=requires_human_review,
            has_candidate_evidence=(candidate_count > 0),
            response_version="1.0",
        )

        return StructuredAIResponse(
            request_id=request_id,
            query=grounded_response.query,
            status=status,
            answer=grounded_response.answer,
            grounded=grounded_response.grounded,
            gap=grounded_response.gap,
            citations=grounded_response.citations,
            provenance=grounded_response.provenance,
            conflicts=grounded_response.conflicts,
            retrieved_evidence=evidence_items,
            metadata=metadata,
        )

    @classmethod
    def map_external_status(cls, response: StructuredAIResponse) -> str:
        """Map internal StructuredAIResponse to external product/frontend status contract.

        Conforms strictly to W4.11 Contract Section 7.A:
        - SUCCESS: Grounded answer supported by retrieved evidence without conflicts
        - CONFLICT_DETECTED: Documented regulatory overlap or contradiction among sources
        - GAP_DETECTED: Insufficient evidence, missing provision, or out-of-scope query
        - NO_SOURCE_FOUND: Fail-closed unapproved evidence or zero matching records
        - ERROR: Technical or unhandled pipeline exception
        """
        if response.status == ResponseStatus.ERROR:
            return "ERROR"
        if response.status == ResponseStatus.UNAPPROVED_EVIDENCE or (
            response.gap and response.gap.gap_type == GapType.NO_RETRIEVED_EVIDENCE
        ):
            return "NO_SOURCE_FOUND"
        if response.status in (ResponseStatus.INSUFFICIENT_EVIDENCE, ResponseStatus.OUT_OF_SCOPE):
            return "GAP_DETECTED"
        if response.status == ResponseStatus.CONFLICTING_EVIDENCE or (
            response.status == ResponseStatus.GROUNDED and len(response.conflicts) > 0
        ):
            return "CONFLICT_DETECTED"
        if response.status == ResponseStatus.GROUNDED:
            return "SUCCESS"
        if response.gap and response.gap.is_gap:
            return "GAP_DETECTED"
        return "SUCCESS"
