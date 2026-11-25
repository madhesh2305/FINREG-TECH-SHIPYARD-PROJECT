"""Advice comparison endpoint for Week 5 Task W5.5."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
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
        "Performs source-grounded comparison between Advisor 1 and Advisor 2.\n\n"
        "### Architectural Contract & Integration Flow:\n"
        "**Frontend (Vite) → Main Backend Gateway (port 8000) → AI/RAG Microservice (port 8001)**\n\n"
        "1. **Frontend Calling Pattern**: The frontend must NOT call this microservice directly with advisor IDs. "
        "Instead, the frontend calls `POST /api/v1/projects/{projectId}/compare-advice` on the Main Backend Gateway (port 8000).\n"
        "2. **Backend Gateway Responsibilities**:\n"
        "   - Authenticates the user (JWT validation).\n"
        "   - Verifies project membership and authorization for `{projectId}`.\n"
        "   - Fetches both advisor advice records from PostgreSQL using the supplied advisor IDs.\n"
        "   - Validates that both advice records belong to the authorized project.\n"
        "   - Constructs complete advisor objects containing their actual `advice_text`.\n"
        "   - Forwards the full comparison payload to the AI/RAG microservice on port 8001 (`POST /api/v1/compare`).\n"
        "   - Returns the structured AI/RAG comparison response back to the frontend.\n"
        "3. **AI/RAG Microservice Scope**:\n"
        "   - Does **NOT** connect to PostgreSQL or manage database dependencies.\n"
        "   - Does **NOT** resolve bare advisor IDs (both `advisor_1` and `advisor_2` MUST provide full `advice_text`).\n"
        "   - Receives complete advisor objects and performs semantic comparison, difference categorization, "
        "evidence retrieval from ChromaDB, citation/provenance attachment, and regulatory conflict detection.\n"
        "   - Strictly non-adjudicative: always preserves `decision: null` for human SME disposition.\n\n"
        "### Request Formats Supported:\n"
        "1. **Format A – Complete Advisor Objects (Normal Path)**:\n"
        "   Both `advisor_1` and `advisor_2` are provided with full `advice_text`. Returns HTTP 200 with complete comparison.\n"
        "2. **Format B – Advisor IDs Only (Gateway Unresolved Path)**:\n"
        "   `advisor_1_id` and `advisor_2_id` are provided without advice text. Safely returns HTTP 409 Conflict "
        "(`ADVISOR_DATA_NOT_RESOLVED`), instructing the Backend Gateway to fetch advice from PostgreSQL.\n\n"
        "### Example Format A (Complete Objects):\n"
        "```json\n"
        "{\n"
        '  "project_id": "PRJ-ABC-001",\n'
        '  "advisor_1": {\n'
        '    "advice_id": "ADV-001",\n'
        '    "advice_text": "Commercial organisations are strictly liable under Section 7 unless they prove adequate procedures.",\n'
        '    "advisor_name": "Counsel Alpha"\n'
        "  },\n"
        '  "advisor_2": {\n'
        '    "advice_id": "ADV-002",\n'
        '    "advice_text": "Commercial organisations bear the burden of establishing reasonable prevention procedures.",\n'
        '    "advisor_name": "Counsel Beta"\n'
        "  },\n"
        '  "context": {\n'
        '    "jurisdiction": "UK"\n'
        "  }\n"
        "}\n"
        "```\n\n"
        "### Example Format B (Advisor IDs Only):\n"
        "```json\n"
        "{\n"
        '  "project_id": "PRJ-ABC-001",\n'
        '  "advisor_1_id": "ADV-001",\n'
        '  "advisor_2_id": "ADV-002"\n'
        "}\n"
        "```\n\n"
        "### Format B HTTP 409 Conflict Response:\n"
        "```json\n"
        "{\n"
        '  "status": "ADVISOR_DATA_NOT_RESOLVED",\n'
        '  "error": "Advisor advice text not provided",\n'
        '  "detail": "Received bare advisor identifiers...",\n'
        '  "advisor_1_id": "ADV-001",\n'
        '  "advisor_2_id": "ADV-002",\n'
        '  "project_id": "PRJ-ABC-001",\n'
        '  "decision": null,\n'
        '  "grounded": false\n'
        "}\n"
        "```"
    ),
    responses={
        200: {
            "description": "Successful comparison result with grounded evidence, differences, relationships, and decision=null.",
            "model": AdviceComparisonResult,
        },
        409: {
            "description": "Conflict: Bare advisor IDs provided without advice text. Gateway resolution required.",
        },
        422: {"description": "Validation error (e.g. missing required advice_text, incomplete advisor pairs, or invalid field types)."},
        500: {"description": "Internal server error during comparison execution."},
    },
)
@router.post(
    "/projects/{projectId}/compare-advice",
    response_model=AdviceComparisonResult,
    status_code=status.HTTP_200_OK,
    summary="Compare two advisor advice positions (Gateway & Builder Route)",
    description="Endpoint for project-scoped advice comparison matching Gateway route contract.",
    responses={
        200: {
            "description": "Successful comparison result with grounded evidence, differences, relationships, and decision=null.",
            "model": AdviceComparisonResult,
        },
        409: {
            "description": "Conflict: Bare advisor IDs provided without advice text. Gateway resolution required.",
        },
        422: {"description": "Validation error (e.g. missing required advice_text, incomplete advisor pairs, or invalid field types)."},
        500: {"description": "Internal server error during comparison execution."},
    },
)
@router.post(
    "/compare-advice",
    response_model=AdviceComparisonResult,
    status_code=status.HTTP_200_OK,
    summary="Compare two advisor advice positions (Alias)",
    description="Alias endpoint for advice comparison.",
    responses={
        200: {
            "description": "Successful comparison result with grounded evidence, differences, relationships, and decision=null.",
            "model": AdviceComparisonResult,
        },
        409: {
            "description": "Conflict: Bare advisor IDs provided without advice text. Gateway resolution required.",
        },
        422: {"description": "Validation error (e.g. missing required advice_text, incomplete advisor pairs, or invalid field types)."},
        500: {"description": "Internal server error during comparison execution."},
    },
)
def compare_advice(
    request: AdviceComparisonRequest,
    projectId: Optional[str] = None,
    comparator: AdviceComparator = Depends(get_advice_comparator),
):
    """Execute source-grounded comparison between two advisor advice records."""
    if projectId and not request.project_id:
        request.project_id = projectId
    # Check if ID-only request format was submitted
    if request.advisor_1 is None or request.advisor_2 is None:
        logger.info(
            "Comparison request received with bare advisor IDs (advisor_1_id=%s, advisor_2_id=%s). "
            "Returning HTTP 409 ADVISOR_DATA_NOT_RESOLVED.",
            request.advisor_1_id,
            request.advisor_2_id,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "status": "ADVISOR_DATA_NOT_RESOLVED",
                "error": "Advisor advice text not provided",
                "detail": (
                    f"Received bare advisor identifiers (advisor_1_id='{request.advisor_1_id}', "
                    f"advisor_2_id='{request.advisor_2_id}'). The AI/RAG microservice does not connect to "
                    "PostgreSQL and cannot resolve bare advisor IDs. The Main Backend Gateway must retrieve "
                    "the actual advisor records from PostgreSQL and forward complete advisor objects with 'advice_text'."
                ),
                "advisor_1_id": request.advisor_1_id,
                "advisor_2_id": request.advisor_2_id,
                "project_id": request.project_id,
                "decision": None,
                "grounded": False,
            },
        )

    try:
        return comparator.compare_from_request(request)
    except Exception as e:
        logger.exception("Unexpected error executing advice comparison: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the advice comparison.",
        )
