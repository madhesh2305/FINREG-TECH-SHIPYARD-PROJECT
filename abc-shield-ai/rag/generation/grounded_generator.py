"""Grounded generator orchestrating retrieval, prompt construction, and LLM generation.

Enforces zero-hallucination guardrails, approval status warnings, and controlled
handling of empty or insufficient evidence.
"""

from typing import List, Optional
import logging
from pydantic import BaseModel, Field

from rag.retrieval.retriever import RegulatoryRetriever, RetrievalResult
from rag.generation.llm_interface import BaseLLMProvider, get_llm_provider
from rag.generation.prompts import (
    SYSTEM_GROUNDING_PROMPT,
    build_evidence_context,
    build_user_prompt,
)
from rag.generation.citations import Citation, ProvenanceRecord, CitationBuilder
from rag.generation.gap_handler import GapType, GapResult, GapHandler
from rag.conflict import ConflictFinding, ConflictDetector

logger = logging.getLogger(__name__)

CANDIDATE_APPROVAL_WARNING = (
    "Development evidence only: the retrieved regulatory records are currently "
    "marked Candidate - Awaiting Approval and have not been approved for authoritative RAG use."
)


class GroundedResponse(BaseModel):
    """Structured response from the Grounded Generator."""

    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Grounded answer text generated from supplied evidence")
    evidence_used: List[str] = Field(
        default_factory=list,
        description="List of Chunk IDs provided as evidence context"
    )
    confidence_status: str = Field(
        ...,
        description="Status indicator: 'GROUNDED', 'INSUFFICIENT_EVIDENCE', or 'EMPTY_RETRIEVAL'"
    )
    grounded: bool = Field(
        ...,
        description="Whether the answer was successfully grounded on supplied evidence"
    )
    approval_warning: Optional[str] = Field(
        None,
        description="Safety warning if unapproved or candidate records were used"
    )
    evidence_count: int = Field(0, description="Total number of evidence chunks supplied to LLM")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Deterministic citations derived strictly from retrieved evidence"
    )
    provenance: List[ProvenanceRecord] = Field(
        default_factory=list,
        description="Full traceable provenance records for each cited chunk"
    )
    gap: Optional[GapResult] = Field(
        None,
        description="Structured GAP / No-source analysis result when evidence is insufficient or missing"
    )
    conflicts: List[ConflictFinding] = Field(
        default_factory=list,
        description="Documented regulatory conflict and overlap findings identified in retrieved evidence"
    )

    def to_structured_response(
        self,
        retrieved_chunks: Optional[List[RetrievalResult]] = None,
        request_id: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Convert this GroundedResponse into the unified Task 9 StructuredAIResponse contract."""
        from rag.output.response_builder import StructuredResponseBuilder
        return StructuredResponseBuilder.build(
            grounded_response=self,
            retrieved_chunks=retrieved_chunks,
            request_id=request_id,
            error=error,
        )


class GroundedGenerator:
    """Orchestrates retrieval and grounded LLM generation with strict safety guardrails."""

    def __init__(
        self,
        retriever: Optional[RegulatoryRetriever] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        self.retriever = retriever or RegulatoryRetriever()
        self.llm_provider = llm_provider or get_llm_provider()
        self.conflict_detector = conflict_detector or ConflictDetector()

    def generate_response(
        self,
        query: str,
        top_k: int = 5,
        jurisdiction: Optional[str] = None,
        filter_approved_only: bool = False,
        evidence_chunks: Optional[List[RetrievalResult]] = None,
        project_id: Optional[str] = None,
    ) -> GroundedResponse:
        """Execute grounded generation for a natural-language regulatory query.

        Args:
            query: The user's regulatory question.
            top_k: Number of evidence chunks to retrieve.
            jurisdiction: Optional jurisdiction filter ('UK', 'EU').
            filter_approved_only: If True, only queries approved authoritative records.
            evidence_chunks: Optional pre-retrieved evidence chunks to avoid duplicate retrieval.
            project_id: Optional project or tenant identifier for isolation.

        Returns:
            GroundedResponse with structured fields and safety warnings.
        """
        clean_query = query.strip()
        if not clean_query:
            return GroundedResponse(
                query=query,
                answer="No query provided. Please specify a regulatory question.",
                evidence_used=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                grounded=False,
                approval_warning=None,
                evidence_count=0,
            )

        # 1. Retrieve evidence chunks from vector database if not pre-supplied
        if evidence_chunks is None:
            evidence_chunks = self.retriever.retrieve(
                query=clean_query,
                top_k=top_k,
                jurisdiction=jurisdiction,
                filter_approved_only=filter_approved_only,
                project_id=project_id,
            )

        # 2. Safety Rule: Handle empty retrieval WITHOUT calling the LLM
        if not evidence_chunks:
            logger.info("Zero evidence chunks retrieved for query: '%s'. Skipping LLM call.", clean_query)
            gap = GapHandler.analyze_gap(
                query=clean_query,
                retrieved_chunks=[],
                is_grounded=False,
                filter_approved_only=filter_approved_only,
            )
            return GroundedResponse(
                query=clean_query,
                answer="The available regulatory evidence is insufficient to answer this question. No matching regulatory records were found.",
                evidence_used=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                grounded=False,
                approval_warning=None,
                evidence_count=0,
                citations=[],
                provenance=[],
                gap=gap,
                conflicts=[],
            )

        # 2b. Safety Rule: Handle Out-of-Scope queries WITHOUT calling the LLM (RAG-011)
        detected_domain = GapHandler._detect_out_of_scope(clean_query.lower())
        if detected_domain:
            gap = GapHandler.analyze_gap(
                query=clean_query,
                retrieved_chunks=evidence_chunks,
                is_grounded=False,
                filter_approved_only=filter_approved_only,
            )
            return GroundedResponse(
                query=clean_query,
                answer=(
                    f"The current ABC Shield scope does not provide sufficient evidence (insufficient evidence) for {detected_domain}. "
                    "(Scope is strictly limited to UK and EU anti-bribery and anti-corruption frameworks, "
                    "and relevant FCA financial-crime systems and controls)."
                ),
                evidence_used=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                grounded=False,
                approval_warning=None,
                evidence_count=0,
                citations=[],
                provenance=[],
                gap=gap,
                conflicts=[],
            )

        # 2c. Safety Rule: Handle Unsupported National Transposition queries (RAG-012)
        unsupported_jur = GapHandler._detect_unsupported_transposition(clean_query.lower())
        if unsupported_jur:
            gap = GapResult(
                is_gap=True,
                gap_type=GapType.DATA_COVERAGE_LIMITATION,
                message=f"Query requests national transposing legislation in {unsupported_jur}, which is outside the canonical ABC Shield corpus.",
                user_safe_message=(
                    f"The ABC Shield regulatory corpus covers EU-level Directive provisions and UK legislation, but does not contain national transposing legislation for {unsupported_jur}. "
                    "Member-state transposition requires specific national legal sources and Compliance SME verification."
                ),
                retrieved_chunk_ids=[c.chunk_id for c in evidence_chunks],
                retrieved_record_ids=list(dict.fromkeys(c.record_id for c in evidence_chunks)),
                relevant_evidence_count=len(evidence_chunks),
                approved_evidence_count=0,
                has_candidate_evidence=True,
                requires_human_review=True,
                coverage_nature="CORPUS_COVERAGE_LIMITATION",
                recommended_next_action=f"Obtain and verify the official member-state transposition source for {unsupported_jur}.",
            )
            return GroundedResponse(
                query=clean_query,
                answer=(
                    f"The available regulatory evidence is insufficient to answer what exact national law implements the requested provisions in {unsupported_jur}. "
                    "The ABC Shield regulatory corpus covers EU-level Directive provisions and UK anti-bribery legislation, but does not contain member-state national transposing laws. "
                    "National transposition details require specific local legal sources and authorised Compliance SME verification."
                ),
                evidence_used=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                grounded=False,
                approval_warning=None,
                evidence_count=0,
                citations=[],
                provenance=[],
                gap=gap,
                conflicts=[],
            )

        # 3. Provenance Integrity Guardrail (RAG-04 / RAG-13): Filter untrusted or tampered chunks
        trusted_chunks = [c for c in evidence_chunks if CitationBuilder.is_valid_provenance(c)]
        if not trusted_chunks:
            logger.warning("All evidence chunks lack trusted provenance or have manipulated metadata. Failing closed.")
            gap = GapResult(
                is_gap=True,
                gap_type=GapType.NEEDS_HUMAN_REVIEW,
                message="Retrieved or supplied evidence lacks valid trusted provenance (source_id, chunk_id, or section/article missing or corrupted).",
                user_safe_message="The available regulatory evidence cannot be verified due to missing or untrusted provenance information.",
                retrieved_chunk_ids=[],
                retrieved_record_ids=[],
                relevant_evidence_count=0,
                approved_evidence_count=0,
                has_candidate_evidence=False,
                requires_human_review=True,
                coverage_nature="NEEDS_HUMAN_REVIEW",
                recommended_next_action="Review data provenance and source register alignment with a compliance SME.",
            )
            return GroundedResponse(
                query=clean_query,
                answer="The available regulatory evidence cannot be verified due to missing or untrusted provenance information.",
                evidence_used=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                grounded=False,
                approval_warning=None,
                evidence_count=0,
                citations=[],
                provenance=[],
                gap=gap,
                conflicts=[],
            )

        evidence_chunks = trusted_chunks

        # 4. Safety Rule: Check approval status across all retrieved evidence
        is_candidate_evidence = any(not chunk.is_approved_for_rag for chunk in evidence_chunks)
        approval_warning = CANDIDATE_APPROVAL_WARNING if is_candidate_evidence else None

        # 4. Construct deterministic context and prompt
        evidence_context = build_evidence_context(evidence_chunks)
        user_prompt = build_user_prompt(clean_query, evidence_context)
        chunk_ids = [c.chunk_id for c in evidence_chunks]

        # 5. Call provider-independent LLM
        raw_answer = self.llm_provider.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_GROUNDING_PROMPT,
        )

        # 6. Determine grounding status
        answer_lower = raw_answer.lower()
        is_insufficient = (
            "insufficient" in answer_lower
            or "no provisions" in answer_lower
            or "not covered" in answer_lower
            or "no regulatory evidence" in answer_lower
        )

        if is_insufficient:
            confidence_status = "INSUFFICIENT_EVIDENCE"
            grounded = False
        else:
            confidence_status = "GROUNDED"
            grounded = True

        # 7. Construct deterministic citation and provenance records
        citations, provenance = CitationBuilder.build_citations(
            retrieved_chunks=evidence_chunks,
            is_grounded=grounded,
        )

        # 8. Deterministic Conflict / Overlap analysis
        conflicts = self.conflict_detector.detect(evidence_chunks)

        # 9. Deterministic GAP / No-source analysis
        gap = GapHandler.analyze_gap(
            query=clean_query,
            retrieved_chunks=evidence_chunks,
            is_grounded=grounded,
            raw_answer=raw_answer,
            filter_approved_only=filter_approved_only,
            conflicts=conflicts,
        )

        return GroundedResponse(
            query=clean_query,
            answer=raw_answer.strip(),
            evidence_used=chunk_ids,
            confidence_status=confidence_status,
            grounded=grounded,
            approval_warning=approval_warning,
            evidence_count=len(evidence_chunks),
            citations=citations,
            provenance=provenance,
            gap=gap,
            conflicts=conflicts,
        )

    def generate_structured_response(
        self,
        query: str,
        top_k: int = 5,
        jurisdiction: Optional[str] = None,
        filter_approved_only: bool = False,
        request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        evidence_chunks: Optional[List[RetrievalResult]] = None,
    ):
        """Execute grounded generation and assemble the unified Task 9 StructuredAIResponse contract.

        Reuses retrieval results without querying ChromaDB multiple times.
        """
        from rag.output.response_builder import StructuredResponseBuilder

        clean_query = query.strip()
        if not clean_query:
            resp = self.generate_response(query=query, project_id=project_id)
            return StructuredResponseBuilder.build(
                grounded_response=resp,
                retrieved_chunks=[],
                request_id=request_id,
            )

        # Single retrieval step if not pre-supplied
        if evidence_chunks is None:
            evidence_chunks = self.retriever.retrieve(
                query=clean_query,
                top_k=top_k,
                jurisdiction=jurisdiction,
                filter_approved_only=filter_approved_only,
                project_id=project_id,
            )

        # Generate response using retrieved chunks
        grounded_resp = self.generate_response(
            query=clean_query,
            top_k=top_k,
            jurisdiction=jurisdiction,
            filter_approved_only=filter_approved_only,
            evidence_chunks=evidence_chunks,
            project_id=project_id,
        )

        # Assemble unified machine-readable response
        return StructuredResponseBuilder.build(
            grounded_response=grounded_resp,
            retrieved_chunks=evidence_chunks,
            request_id=request_id,
        )


class StagedGroundedGenerator(GroundedGenerator):
    """Grounded generator configured strictly for staging evaluation against the canonical 25 corpus.

    Ensures that queries retrieve from the staged ChromaDB and that all generated responses
    retain unapproved candidate warnings and strict evidence provenance.
    """

    def __init__(
        self,
        retriever: Optional[RegulatoryRetriever] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        conflict_detector: Optional[ConflictDetector] = None,
    ):
        from rag.retrieval.retriever import StagedRegulatoryRetriever
        staged_retriever = retriever or StagedRegulatoryRetriever()
        super().__init__(
            retriever=staged_retriever,
            llm_provider=llm_provider,
            conflict_detector=conflict_detector,
        )

