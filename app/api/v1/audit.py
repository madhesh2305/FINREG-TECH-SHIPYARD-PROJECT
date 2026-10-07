from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.project import ProjectMember
from app.schemas.audit import AuditEventResponse
from app.security.authorization import require_project_member
from app.services.audit_service import list_project_audit_events

router = APIRouter(prefix="/projects/{projectId}/audit-events", tags=["Audit Log"])

@router.get(
    "",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Audit Events",
    description="Returns chronological immutable audit trail for the project. Caller must be an active project member."
)
def get_audit_events(
    projectId: int,
    event_type: Optional[str] = Query(None, description="Filter by event type, e.g. PROJECT_CREATED, MEMBER_ADDED"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    events = list_project_audit_events(db=db, project_id=projectId, event_type=event_type, limit=limit)
    return [
        AuditEventResponse(
            audit_event_id=e.audit_event_id,
            project_id=e.project_id,
            actor_user_id=e.actor_user_id,
            actor_name=e.actor.full_name if e.actor else "System",
            event_type=e.event_type,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            old_values=e.old_values or {},
            new_values=e.new_values or {},
            event_description=e.event_description,
            created_at=e.created_at
        )
        for e in events
    ]
