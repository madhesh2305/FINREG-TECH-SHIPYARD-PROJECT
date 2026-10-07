from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.decision import DecisionCreate, DecisionResponse
from app.services.decision_service import (
    record_decision,
    list_project_decisions,
    get_decision_by_id,
)
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member, require_project_owner

router = APIRouter(prefix="/projects/{projectId}/decisions", tags=["Compliance Decisions"])

@router.post(
    "",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Authoritative Compliance Decision",
    description="Allows project owners to record binding compliance decisions (ACCEPT, REJECT, REVIEW_REQUIRED, FOLLOW_UP_REQUIRED) with executive rationale and follow-up actions."
)
def create_decision(
    projectId: int,
    request: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: ProjectMember = Depends(require_project_owner),
):
    return record_decision(db=db, project_id=projectId, request=request, actor=current_user)

@router.get(
    "",
    response_model=List[DecisionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Compliance Decisions",
    description="Retrieves the full decision history for a compliance project."
)
def get_all_decisions(
    projectId: int,
    db: Session = Depends(get_db),
    _membership: ProjectMember = Depends(require_project_member),
):
    return list_project_decisions(db=db, project_id=projectId)

@router.get(
    "/{decisionId}",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Compliance Decision",
    description="Retrieves an individual compliance decision with decider details and audit trail."
)
def get_single_decision(
    projectId: int,
    decisionId: int,
    db: Session = Depends(get_db),
    _membership: ProjectMember = Depends(require_project_member),
):
    return get_decision_by_id(db=db, project_id=projectId, decision_id=decisionId)
