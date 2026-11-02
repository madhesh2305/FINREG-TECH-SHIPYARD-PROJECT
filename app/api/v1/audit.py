from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import Project, ProjectMember
from app.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member
from app.services.audit_service import list_project_audit_events, list_all_audit_events

router = APIRouter(tags=["Audit Log"])

def _build_audit_response(e: AuditEvent, db: Session) -> AuditEventResponse:
    actor_name = e.actor.full_name if e.actor else "System"
    actor_role = e.actor.role.role_name if (e.actor and e.actor.role) else "Platform"
    project_code = e.project.project_code if e.project else None
    return AuditEventResponse(
        audit_event_id=e.audit_event_id,
        project_id=e.project_id,
        actor_user_id=e.actor_user_id,
        actor_name=actor_name,
        actor_role=actor_role,
        project_code=project_code,
        event_type=e.event_type,
        entity_type=e.entity_type,
        entity_id=e.entity_id,
        old_values=e.old_values or {},
        new_values=e.new_values or {},
        event_description=e.event_description,
        created_at=e.created_at
    )

@router.get(
    "/projects/{projectId}/audit-events",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Audit Events",
    description="Returns chronological immutable audit trail for the project. Caller must be an active project member."
)
def get_audit_events(
    projectId: Union[int, str],
    event_type: Optional[str] = Query(None, description="Filter by event type, e.g. PROJECT_CREATED, MEMBER_ADDED"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    events = list_project_audit_events(db=db, project_id=membership.project_id, event_type=event_type, limit=limit)
    return [_build_audit_response(e, db) for e in events]

@router.get(
    "/audit",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Scoped / Platform Audit Events",
    description="Returns authorized audit events. Admin sees all events; users see events scoped to their active projects (DEF-31)."
)
@router.get(
    "/audit-events",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Scoped / Platform Audit Events",
    description="Alias endpoint for listing authorized audit events (DEF-31)."
)
def list_global_audit_events(
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    is_admin = current_user.role and current_user.role.role_name and current_user.role.role_name.upper() == "ADMIN"
    if is_admin:
        events = list_all_audit_events(db=db, event_type=event_type, limit=limit)
    else:
        user_pids = [
            r[0] for r in db.query(ProjectMember.project_id)
            .filter(ProjectMember.user_id == current_user.user_id, ProjectMember.member_status == "ACTIVE")
            .all()
        ]
        created_pids = [
            r[0] for r in db.query(Project.project_id)
            .filter(Project.created_by == current_user.user_id)
            .all()
        ]
        all_pids = list(set(user_pids + created_pids))
        query = db.query(AuditEvent).filter(
            (AuditEvent.project_id.in_(all_pids)) | (AuditEvent.actor_user_id == current_user.user_id)
        )
        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        events = query.order_by(AuditEvent.created_at.desc()).limit(limit).all()

    return [_build_audit_response(e, db) for e in events]
