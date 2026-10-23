"""Advice comparison endpoint for Week 5 Task W5.5."""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from api.dependencies import get_advice_comparator
from rag.pipeline.advice_comparator import (
    AdviceComparator,
    AdviceComparisonRequest,
    AdviceComparisonResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Advice Comparison"])


@router.post(
    "/compare",
    response_model=AdviceComparisonResult,
    status_code=status.HTTP_200_OK,
    summary="Compare two advisor advice positions against regulatory evidence",
    description=(
        "Performs source-grounded comparison between Advisor 1 and Advisor 2. "
        "Identifies differences, contradictions, scope/authority/version differences, "
        "retrieves supporting regulatory evidence, attaches citations/provenance, "
        "and detects registered regulatory conflicts and evidence gaps. "
        "Strictly non-adjudicative: preserves decision=None for human SME disposition."
    ),
    responses={
        200: {
            "description": "Successful comparison result. Note that contradictions, conflicts, and gaps return HTTP 200 with human_review_required=True.",
            "model": AdviceComparisonResult,
        },
        422: {"description": "Validation error (e.g. empty advice text or unauthorized extra fields)"},
        500: {"description": "Internal server error during comparison execution"},
    },
)
def compare_advice(
    request: AdviceComparisonRequest,
    comparator: AdviceComparator = Depends(get_advice_comparator),
) -> AdviceComparisonResult:
    """Execute source-grounded comparison between two advisor advice records."""
    try:
        return comparator.compare_from_request(request)
    except Exception as e:
        logger.exception("Unexpected error executing advice comparison: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the advice comparison.",
        )
