import uuid
import logging
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project, ProjectMember
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.models.advice import Advice
from app.schemas.ai import (
    RetrievalRequest,
    RetrievalResponse,
    RAGAnalyzeRequest,
    RAGCompareRequest,
    AdviceItemPayload,
)
from app.security.authorization import require_project_member
from app.security.authentication import get_current_user
from app.models.identity import User
from app.services.ai_service import retrieve_grounded_sources
from app.services.rag_service import get_rag_service_client, format_rag_response_for_frontend
from app.core.exceptions import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Copilot & Intelligence"])


@router.post(
    "/projects/{projectId}/ai/retrieve",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Grounded Regulatory Retrieval",
    description="Retrieves evidence-backed regulatory citations matching the query from verified corpus. Returns NO_SOURCE_FOUND if no evidence exists. Never fabricates citations."
)
def retrieve_citations(
    projectId: Union[int, str],
    request: RetrievalRequest,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return retrieve_grounded_sources(db=db, project_id=membership.project_id, request=request)


@router.get(
    "/rag/health",
    status_code=status.HTTP_200_OK,
    summary="RAG Microservice Health Check",
    description="Probes the connectivity and readiness of the internal ABC Shield AI/RAG microservice.",
)
def rag_service_health():
    """Verify live connectivity from the ShipYard backend to the ABC Shield RAG microservice."""
    client = get_rag_service_client()
    health_data = client.check_health()
    return {
        "status": "healthy" if health_data.get("status") == "connected" else "degraded",
        "service": "FinRegTech ShipYard Backend",
        "rag_microservice": health_data,
    }


@router.post(
    "/rag/compare",
    status_code=status.HTTP_200_OK,
    summary="Compare Advisor Advice Positions",
    description="Compares two advisor positions against the canonical ABC Shield regulatory corpus. Enforces project access and non-adjudication.",
)
def compare_advisor_advice(
    payload: RAGCompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare two advisor advice positions using the ABC Shield RAG comparator."""
    if not current_user:
        raise AuthenticationError("Authentication required to access regulatory comparison.")

    # Project access validation if projectId / project_id provided
    project = None
    target_pid = payload.resolved_project_id
    if target_pid is not None:
        raw_pid = target_pid
        if isinstance(raw_pid, int) or (isinstance(raw_pid, str) and str(raw_pid).isdigit()):
            project = db.query(Project).filter(Project.project_id == int(raw_pid)).first()
        else:
            project = db.query(Project).filter(Project.project_code == str(raw_pid)).first()

        if not project:
            raise NotFoundError(f"Project '{target_pid}' not found")

        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.project_id,
            ProjectMember.user_id == current_user.user_id,
            ProjectMember.member_status == "ACTIVE"
        ).first()
        if not membership:
            raise ForbiddenError(f"User is not an active member of project '{target_pid}'")

    client = get_rag_service_client()
    raw_comp = client.compare_advice(
        advisor_1=payload.advisor_1.model_dump(),
        advisor_2=payload.advisor_2.model_dump(),
        comparison_id=payload.comparison_id,
        project_id=project.project_id if project else None,
        context=payload.context,
    )
    return format_rag_response_for_frontend(
        raw_comp,
        query_text=f"Comparison: {payload.advisor_1.advisor_name or 'Advisor 1'} vs {payload.advisor_2.advisor_name or 'Advisor 2'}",
        project_id=project.project_id if project else None,
    )


@router.post(
    "/rag/analyze",
    status_code=status.HTTP_200_OK,
    summary="Grounded RAG & Conflict Analysis",
    description="Authenticates caller, validates project authorization, queries ABC Shield AI/RAG microservice, and returns structured findings.",
)
def analyze_rag(
    payload: RAGAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute authenticated, project-isolated regulatory analysis via the ABC Shield RAG microservice."""
    # 1. Mandatory Authentication Check
    if not current_user:
        raise AuthenticationError("Authentication required to access regulatory AI intelligence.")

    # 2. Query Validation
    query_text = payload.query.strip() if payload.query else ""
    if not query_text:
        raise ValidationError("Query cannot be empty or whitespace-only.")

    # 3. Project Authorization & Isolation Check
    project = None
    target_pid = payload.resolved_project_id
    if target_pid is not None:
        raw_pid = target_pid
        if isinstance(raw_pid, int) or (isinstance(raw_pid, str) and str(raw_pid).isdigit()):
            project = db.query(Project).filter(Project.project_id == int(raw_pid)).first()
        else:
            project = db.query(Project).filter(Project.project_code == str(raw_pid)).first()
            if not project and str(raw_pid).upper() in ("PRJ-001", "PRJ-1"):
                project = db.query(Project).filter(
                    (Project.project_id == 1) | (Project.project_code == "PRJ-ABC-001")
                ).first()

        if not project:
            raise NotFoundError(f"Project '{target_pid}' not found")

        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.project_id,
            ProjectMember.user_id == current_user.user_id,
            ProjectMember.member_status == "ACTIVE"
        ).first()
        if not membership:
            raise ForbiddenError(f"You are not an active member of project '{target_pid}'")

        # Validate requirement_ids (BOLA defense)
        if payload.requirement_ids:
            for req_code in payload.requirement_ids:
                req = db.query(RegulatoryRequirement).filter(
                    RegulatoryRequirement.project_id == project.project_id,
                    (RegulatoryRequirement.requirement_code == req_code)
                    | (RegulatoryRequirement.requirement_id == int(req_code) if str(req_code).isdigit() else False)
                ).first()
                if not req:
                    raise NotFoundError(f"Requirement '{req_code}' not found in project '{target_pid}'")

        # Validate advisor_advice_ids (BOLA defense)
        if payload.advisor_advice_ids:
            for adv_id in payload.advisor_advice_ids:
                if str(adv_id).isdigit():
                    adv = db.query(Advice).filter(
                        Advice.project_id == project.project_id,
                        Advice.advice_id == int(adv_id)
                    ).first()
                    if not adv:
                        raise NotFoundError(f"Advice '{adv_id}' not found in project '{target_pid}'")
    else:
        # If no projectId provided, project-specific resources cannot be attached
        if payload.advisor_advice_ids or payload.requirement_ids:
            raise ValidationError("projectId or project_id is required when referencing project requirements or advisor advice.")

    rag_client = get_rag_service_client()

    # 4. Project Advice Comparison (from DB records when advice IDs requested)
    if project and payload.advisor_advice_ids and len(payload.advisor_advice_ids) >= 2:
        adv_ids = [int(x) for x in payload.advisor_advice_ids[:2] if str(x).isdigit()]
        adv_records = db.query(Advice).filter(
            Advice.project_id == project.project_id,
            Advice.advice_id.in_(adv_ids)
        ).all()

        if len(adv_records) >= 2:
            a1, a2 = adv_records[0], adv_records[1]
            advisor_1 = {
                "advice_id": f"ADV-{a1.advice_id}",
                "advisor_name": f"Advisor Profile {a1.advisor_profile_id}",
                "advice_text": a1.advice_text or a1.recommendation or a1.title,
                "source_reference": a1.title,
            }
            advisor_2 = {
                "advice_id": f"ADV-{a2.advice_id}",
                "advisor_name": f"Advisor Profile {a2.advisor_profile_id}",
                "advice_text": a2.advice_text or a2.recommendation or a2.title,
                "source_reference": a2.title,
            }
            raw_comp = rag_client.compare_advice(
                advisor_1=advisor_1,
                advisor_2=advisor_2,
                comparison_id=f"CMP-{uuid.uuid4().hex[:6].upper()}",
                project_id=project.project_id,
                context=payload.context,
            )
            return format_rag_response_for_frontend(raw_comp, query_text=query_text, project_id=project.project_id)

    # 5. Standard Grounded Regulatory RAG Query
    raw_response = rag_client.query_rag(
        query=query_text,
        project_id=project.project_id if project else None,
        requirement_ids=payload.requirement_ids,
        advisor_advice_ids=payload.advisor_advice_ids,
        context=payload.context,
    )
    return format_rag_response_for_frontend(raw_response, query_text=query_text, project_id=project.project_id if project else None)
