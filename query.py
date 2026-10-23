"""Regulatory intelligence query endpoint for Task 11 and Week 5."""

from fastapi import APIRouter, Depends, HTTPException, status
import uuid
import logging

from api.models.query import QueryRequest
from api.dependencies import get_grounded_generator
from rag.generation.grounded_generator import GroundedGenerator
from rag.output.structured_response import StructuredAIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Regulatory Intelligence"])


@router.post(
    "/query",
    response_model=StructuredAIResponse,
    status_code=status.HTTP_200_OK,
    summary="Query regulatory compliance knowledge base",
    description=(
        "Executes grounded regulatory RAG across the candidate/approved corpus. "
        "Returns a complete StructuredAIResponse including grounded answer, citations, "
        "audit provenance, evidence gaps, documented conflict/overlap findings, and operational metadata. "
        "Supports backend integration context: project_id, requirement_ids, and context dictionary."
    ),
    responses={
        200: {
            "description": "Successful execution of the RAG pipeline. Note that evidence gaps (OUT_OF_SCOPE, INSUFFICIENT_EVIDENCE, UNAPPROVED_EVIDENCE) return HTTP 200 with appropriate ResponseStatus.",
            "model": StructuredAIResponse,
        },
        422: {"description": "Validation error (e.g. empty, whitespace-only, or oversized query)"},
        500: {"description": "Internal server error during pipeline execution"},
    },
)
def execute_query(
    request: QueryRequest,
    generator: GroundedGenerator = Depends(get_grounded_generator),
) -> StructuredAIResponse:
    """Execute the existing RAG pipeline and return the unified StructuredAIResponse."""
    request_id = request.id.strip() if request.id and request.id.strip() else f"REQ-{uuid.uuid4()}"

    # Extract integration context supported by the existing RAG engine
    project_id = request.project_id.strip() if request.project_id and request.project_id.strip() else None

    jurisdiction = None
    filter_approved_only = False
    if request.context and isinstance(request.context, dict):
        raw_jur = request.context.get("jurisdiction")
        if raw_jur and isinstance(raw_jur, str) and raw_jur.strip():
            jurisdiction = raw_jur.strip()
        raw_approved = request.context.get("filter_approved_only")
        if raw_approved is None:
            raw_approved = request.context.get("approved_only")
        if raw_approved is not None:
            filter_approved_only = bool(raw_approved)

    logger.info(
        "Received query request [%s]: '%.60s...' (project_id=%s, requirement_ids=%s, advisor_advice_ids=%s, jurisdiction=%s, filter_approved_only=%s)",
        request_id,
        request.query,
        project_id,
        request.requirement_ids,
        request.advisor_advice_ids,
        jurisdiction,
        filter_approved_only,
    )

    try:
        from rag.pipeline.advice_adapter import AdviceRAGAdapter
        adapter = AdviceRAGAdapter(generator=generator)
        result = adapter.execute_from_request(
            request,
            filter_approved_only=filter_approved_only,
            raise_exceptions=True,
        )
        response: StructuredAIResponse = result.response
        logger.info(
            "Query [%s] completed with status: %s (grounded=%s, citations=%d, conflicts=%d, workflow_status=%s)",
            request_id,
            response.status.value,
            response.grounded,
            len(response.citations),
            len(response.conflicts),
            result.workflow_status,
        )
        return response
    except Exception as e:
        logger.exception("Unexpected error executing regulatory query [%s]: %s", request_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the regulatory query.",
        )

