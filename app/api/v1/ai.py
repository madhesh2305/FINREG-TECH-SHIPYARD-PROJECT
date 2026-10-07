from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.project import ProjectMember
from app.schemas.ai import RetrievalRequest, RetrievalResponse
from app.security.authorization import require_project_member
from app.services.ai_service import retrieve_grounded_sources

router = APIRouter(prefix="/projects/{projectId}/ai", tags=["AI Copilot & Intelligence"])

@router.post(
    "/retrieve",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Grounded Regulatory Retrieval",
    description="Retrieves evidence-backed regulatory citations matching the query from verified corpus. Returns NO_SOURCE_FOUND if no evidence exists. Never fabricates citations."
)
def retrieve_citations(
    projectId: int,
    request: RetrievalRequest,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return retrieve_grounded_sources(db=db, project_id=projectId, request=request)
