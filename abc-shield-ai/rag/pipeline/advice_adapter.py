"""Advice to RAG workflow integration adapter for ABC Shield.

Bridges upstream product Advice workflows (Vishal/Harshini) with the canonical
Padma RAG engine, providing request normalization, correlation/traceability tracking,
W4.11 external status mapping, and advice workflow status determination.
Preserves strict source grounding, non-adjudication, and security guardrails.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid
import logging
from pydantic import BaseModel, Field, ConfigDict

from api.models.query import QueryRequest
from rag.generation.grounded_generator import GroundedGenerator
from rag.output.structured_response import StructuredAIResponse
from rag.output.response_builder import StructuredResponseBuilder

logger = logging.getLogger(__name__)


class AdviceWorkflowStatus:
    """Canonical workflow status taxonomy for product-level Advice processing.

    Distinct from internal ResponseStatus and W4.11 external RAG status.
    """
    RAG_SUPPORTED = "RAG_SUPPORTED"
    RAG_REVIEW_REQUIRED = "RAG_REVIEW_REQUIRED"
    RAG_GAP_DETECTED = "RAG_GAP_DETECTED"
    RAG_NO_SOURCES = "RAG_NO_SOURCES"
    RAG_ERROR = "RAG_ERROR"


class AdviceTraceabilityContext(BaseModel):
    """Correlation and provenance traceability linking upstream Advice records to RAG output."""
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(..., description="Unique correlation request identifier.")
    project_id: Optional[str] = Field(None, description="Workspace / tenant context.")
    requirement_ids: List[str] = Field(default_factory=list, description="Upstream product requirement IDs.")
    advisor_advice_ids: List[str] = Field(default_factory=list, description="Upstream advisor advice note IDs.")
    jurisdiction: Optional[str] = Field(None, description="Applied jurisdiction context hint.")
    regulatory_area: Optional[str] = Field(None, description="Applied regulatory area context hint.")
    timestamp: str = Field(..., description="ISO 8601 UTC execution timestamp.")


class AdviceRAGResult(BaseModel):
    """Unified result packaging the canonical W4.11 response and advice workflow context."""
    model_config = ConfigDict(extra="forbid")

    response: StructuredAIResponse = Field(..., description="Canonical W4.11 StructuredAIResponse.")
    external_status: str = Field(..., description="W4.11 external status (SUCCESS, CONFLICT_DETECTED, GAP_DETECTED, NO_SOURCE_FOUND, ERROR).")
    workflow_status: str = Field(..., description="Advice workflow status (RAG_SUPPORTED, RAG_REVIEW_REQUIRED, RAG_GAP_DETECTED, RAG_NO_SOURCES, RAG_ERROR).")
    traceability: AdviceTraceabilityContext = Field(..., description="Traceability linking advice records to RAG output.")
    requires_human_review: bool = Field(..., description="Boolean flag indicating if SME human review is mandatory.")
    disclaimer: str = Field(
        default=(
            "This analysis provides source-grounded regulatory intelligence and does not constitute formal legal "
            "or professional advice. Final compliance determinations remain the responsibility of a qualified compliance professional."
        ),
        description="Mandatory non-adjudication and professional advice disclaimer.",
    )

    @property
    def answer(self) -> str:
        return self.response.answer

    @property
    def citations(self):
        return self.response.citations

    @property
    def provenance(self):
        return self.response.provenance

    @property
    def conflicts(self):
        return self.response.conflicts

    @property
    def gap(self):
        return self.response.gap

    def get_evidence_trace(self) -> Dict[str, Any]:
        """Generate a complete traceability trace linking advice query to citations and provenance."""
        return {
            "request_id": self.traceability.request_id,
            "project_id": self.traceability.project_id,
            "requirement_ids": self.traceability.requirement_ids,
            "advisor_advice_ids": self.traceability.advisor_advice_ids,
            "external_status": self.external_status,
            "workflow_status": self.workflow_status,
            "citations": self.citations,
            "provenance": self.provenance,
            "requires_human_review": self.requires_human_review,
        }


class AdviceRAGAdapter:
    """RAG-side integration adapter for the Advice workflow."""

    def __init__(self, generator: Optional[GroundedGenerator] = None):
        if generator is not None:
            self.generator = generator
        else:
            from api.dependencies import get_grounded_generator
            self.generator = get_grounded_generator()

    @classmethod
    def map_workflow_status(cls, external_status: str, requires_human_review: bool) -> str:
        """Map external RAG status and human review flag to Advice workflow status.

        Preserves strict separation between external RAG status and Advice workflow status.
        """
        if external_status == "ERROR":
            return AdviceWorkflowStatus.RAG_ERROR
        if external_status == "NO_SOURCE_FOUND":
            return AdviceWorkflowStatus.RAG_NO_SOURCES
        if external_status == "GAP_DETECTED":
            return AdviceWorkflowStatus.RAG_GAP_DETECTED
        if external_status == "CONFLICT_DETECTED" or requires_human_review:
            return AdviceWorkflowStatus.RAG_REVIEW_REQUIRED
        if external_status == "SUCCESS":
            return AdviceWorkflowStatus.RAG_SUPPORTED
        return AdviceWorkflowStatus.RAG_REVIEW_REQUIRED

    def execute_advice_rag(
        self,
        query: str,
        request_id: Optional[str] = None,
        project_id: Optional[str] = None,
        requirement_ids: Optional[List[str]] = None,
        advisor_advice_ids: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        jurisdiction: Optional[str] = None,
        regulatory_area: Optional[str] = None,
        filter_approved_only: bool = False,
        top_k: int = 5,
        raise_exceptions: bool = True,
    ) -> AdviceRAGResult:
        """Execute grounded RAG for an advice inquiry with full traceability and status mapping.

        Args:
            query: Natural language advice question or compliance topic.
            request_id: Optional client correlation identifier.
            project_id: Optional project / tenant context for workspace isolation.
            requirement_ids: Optional upstream requirement identifiers.
            advisor_advice_ids: Optional advisor advice note identifiers.
            context: Optional filtering dictionary.
            jurisdiction: Optional explicit jurisdiction filter hint ('UK', 'EU').
            regulatory_area: Optional regulatory topic area hint.
            filter_approved_only: Fail-closed gate for approved-only sources.
            top_k: Retrieval depth limit.
            raise_exceptions: If True, re-raises pipeline exceptions; if False, wraps as safe ERROR result.

        Returns:
            AdviceRAGResult packaging StructuredAIResponse, external status, workflow status, and traceability.
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            raise ValueError("Query string cannot be empty or contain only whitespace.")

        req_id = request_id.strip() if request_id and request_id.strip() else f"REQ-{uuid.uuid4()}"
        clean_project_id = project_id.strip() if project_id and project_id.strip() else None

        # Resolve jurisdiction and regulatory area from direct args or context dict
        resolved_jurisdiction = jurisdiction.strip() if jurisdiction and jurisdiction.strip() else None
        resolved_area = regulatory_area.strip() if regulatory_area and regulatory_area.strip() else None

        resolved_filter_approved = filter_approved_only
        if context and isinstance(context, dict):
            if not resolved_jurisdiction:
                jur = context.get("jurisdiction")
                if jur and isinstance(jur, str) and jur.strip():
                    resolved_jurisdiction = jur.strip()
            if not resolved_area:
                area = context.get("regulatory_area")
                if area and isinstance(area, str) and area.strip():
                    resolved_area = area.strip()
            if "filter_approved_only" in context:
                resolved_filter_approved = bool(context["filter_approved_only"])
            elif "approved_only" in context:
                resolved_filter_approved = bool(context["approved_only"])

        req_ids = [r.strip() for r in requirement_ids if r and isinstance(r, str) and r.strip()] if requirement_ids else []
        adv_ids = [a.strip() for a in advisor_advice_ids if a and isinstance(a, str) and a.strip()] if advisor_advice_ids else []

        logger.info(
            "Processing Advice RAG inquiry [%s] (project_id=%s, req_ids=%s, adv_ids=%s, jurisdiction=%s, area=%s, approved_only=%s): '%.60s...'",
            req_id,
            clean_project_id,
            req_ids,
            adv_ids,
            resolved_jurisdiction,
            resolved_area,
            resolved_filter_approved,
            clean_query,
        )

        try:
            response: StructuredAIResponse = self.generator.generate_structured_response(
                query=clean_query,
                top_k=top_k,
                jurisdiction=resolved_jurisdiction,
                filter_approved_only=resolved_filter_approved,
                request_id=req_id,
                project_id=clean_project_id,
            )

            external_status = StructuredResponseBuilder.map_external_status(response)
            requires_human_review = bool(response.metadata.requires_human_review)
            workflow_status = self.map_workflow_status(external_status, requires_human_review)

            traceability = AdviceTraceabilityContext(
                request_id=req_id,
                project_id=clean_project_id,
                requirement_ids=req_ids,
                advisor_advice_ids=adv_ids,
                jurisdiction=resolved_jurisdiction,
                regulatory_area=resolved_area,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AdviceRAGResult(
                response=response,
                external_status=external_status,
                workflow_status=workflow_status,
                traceability=traceability,
                requires_human_review=requires_human_review,
            )

        except Exception as e:
            logger.exception("Unexpected error in Advice RAG execution [%s]: %s", req_id, e)
            if raise_exceptions:
                raise

            # Wrap into safe, masked ERROR result without exposing internals
            from rag.generation.grounded_generator import GroundedResponse
            from rag.output.structured_response import ResponseMetadata, ResponseStatus

            safe_grounded = GroundedResponse(
                query=clean_query,
                answer="An internal server error occurred while processing the regulatory query.",
                evidence_used=[],
                confidence_status="INSUFFICIENT_EVIDENCE",
                grounded=False,
                evidence_count=0,
                citations=[],
                provenance=[],
                conflicts=[],
            )
            safe_response = StructuredResponseBuilder.build(
                grounded_response=safe_grounded,
                retrieved_chunks=[],
                request_id=req_id,
                error="An internal server error occurred while processing the regulatory query.",
            )

            traceability = AdviceTraceabilityContext(
                request_id=req_id,
                project_id=clean_project_id,
                requirement_ids=req_ids,
                advisor_advice_ids=adv_ids,
                jurisdiction=resolved_jurisdiction,
                regulatory_area=resolved_area,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AdviceRAGResult(
                response=safe_response,
                external_status="ERROR",
                workflow_status=AdviceWorkflowStatus.RAG_ERROR,
                traceability=traceability,
                requires_human_review=False,
            )

    def execute_from_request(
        self,
        request: QueryRequest,
        filter_approved_only: bool = False,
        top_k: int = 5,
        raise_exceptions: bool = True,
    ) -> AdviceRAGResult:
        """Execute grounded RAG using a validated QueryRequest model."""
        return self.execute_advice_rag(
            query=request.query,
            request_id=request.id,
            project_id=request.project_id,
            requirement_ids=request.requirement_ids,
            advisor_advice_ids=request.advisor_advice_ids,
            context=request.context,
            filter_approved_only=filter_approved_only,
            top_k=top_k,
            raise_exceptions=raise_exceptions,
        )


__all__ = [
    "AdviceWorkflowStatus",
    "AdviceTraceabilityContext",
    "AdviceRAGResult",
    "AdviceRAGAdapter",
]
