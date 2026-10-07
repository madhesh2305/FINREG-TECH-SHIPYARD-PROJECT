from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.advice import AdviceCreate, AdviceUpdate, AdviceResponse
from app.services.advice_service import (
    submit_advice,
    list_project_advice,
    get_advice_by_id,
    update_advice,
)
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member

router = APIRouter(prefix="/projects/{projectId}/advice", tags=["Advice & Reviews"])

@router.post(
    "",
    response_model=AdviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Project Advisory Review",
    description="Allows advisors to submit formal opinions, recommendations, and regulatory source citations for a project."
)
def create_advice(
    projectId: int,
    request: AdviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: ProjectMember = Depends(require_project_member),
):
    return submit_advice(db=db, project_id=projectId, request=request, actor=current_user)

@router.get(
    "",
    response_model=List[AdviceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Advisory Reviews",
    description="Retrieves all advisory submissions and reviews recorded for the project."
)
def get_all_advice(
    projectId: int,
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, SUBMITTED, REVIEWED, ARCHIVED)"),
    db: Session = Depends(get_db),
    _membership: ProjectMember = Depends(require_project_member),
):
    return list_project_advice(db=db, project_id=projectId, status_filter=status)

@router.get(
    "/{adviceId}",
    response_model=AdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Advisory Review Details",
    description="Retrieves a specific advisory review by ID with source citations and status."
)
def get_single_advice(
    projectId: int,
    adviceId: int,
    db: Session = Depends(get_db),
    _membership: ProjectMember = Depends(require_project_member),
):
    return get_advice_by_id(db=db, project_id=projectId, advice_id=adviceId)

@router.patch(
    "/{adviceId}",
    response_model=AdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Advisory Review / Status Transition",
    description="Updates advice content or status (e.g. project owner reviewing or accepting advice)."
)
def patch_single_advice(
    projectId: int,
    adviceId: int,
    request: AdviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: ProjectMember = Depends(require_project_member),
):
    return update_advice(db=db, project_id=projectId, advice_id=adviceId, request=request, actor=current_user)
