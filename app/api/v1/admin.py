from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import Project
from app.models.regulatory import RegulatorySource
from app.models.audit import AuditEvent
from app.schemas.user import UserResponse
from app.security.authentication import get_current_user
from app.security.authorization import require_platform_role
from app.core.exceptions import NotFoundError, ValidationError
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/admin", tags=["Platform Administration"])

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_projects: int
    regulatory_sources_count: int
    total_audit_events: int

class UserStatusUpdate(BaseModel):
    is_active: bool

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Platform Administration Statistics",
    description="Returns aggregate user, project, regulatory source, and audit counts. Restricted to ADMIN."
)
def get_admin_stats(
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_projects = db.query(Project).count()
    sources_count = db.query(RegulatorySource).count()
    audit_count = db.query(AuditEvent).count()

    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_projects=total_projects,
        regulatory_sources_count=sources_count,
        total_audit_events=audit_count
    )

@router.get(
    "/users",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List Platform Users",
    description="Returns authorized platform user records for user and role management. Restricted to ADMIN."
)
def list_admin_users(
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    results = []
    for u in users:
        results.append(UserResponse(
            user_id=u.user_id,
            full_name=u.full_name,
            email=u.email,
            is_active=u.is_active,
            platform_role=u.role.role_name if u.role else "USER",
            created_at=u.created_at,
            updated_at=u.updated_at
        ))
    return results

@router.patch(
    "/users/{userId}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Account Status",
    description="Activates or deactivates a user account. Restricted to ADMIN."
)
def update_user_status(
    userId: int,
    payload: UserStatusUpdate,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == userId).first()
    if not user:
        raise NotFoundError("User", userId)
    
    # Prevent admin from deactivating self
    if user.user_id == current_user.user_id and not payload.is_active:
        raise ValidationError("Administrator cannot deactivate their own account.")

    old_status = user.is_active
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)

    # Log audit event
    log_audit_event(
        db=db,
        project_id=1,  # Platform level logged to primary project
        actor_user_id=current_user.user_id,
        event_type="USER_STATUS_UPDATED",
        entity_type="USER",
        entity_id=user.user_id,
        event_description=f"User '{user.email}' status changed from {old_status} to {user.is_active}",
        new_values={"is_active": user.is_active}
    )

    return UserResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        platform_role=user.role.role_name if user.role else "USER",
        created_at=user.created_at,
        updated_at=user.updated_at
    )
