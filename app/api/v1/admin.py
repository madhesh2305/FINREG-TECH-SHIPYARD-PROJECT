import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User, Role, RevokedToken
from app.models.project import Project
from app.models.regulatory import RegulatorySource
from app.models.audit import AuditEvent
from app.models.advisor import AdvisorInvitation, AdvisorProfile
from app.schemas.user import UserResponse
from app.schemas.audit import AuditEventResponse
from app.security.authentication import get_current_user
from app.security.authorization import require_platform_role
from app.core.exceptions import NotFoundError, ValidationError, ConflictError, ForbiddenError
from app.services.audit_service import log_audit_event, list_all_audit_events

router = APIRouter(prefix="/admin", tags=["Platform Administration"])

class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_projects: int
    regulatory_sources_count: int
    total_audit_events: int

class UserStatusUpdate(BaseModel):
    is_active: bool

class AdminUserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field("BUILDER", description="Platform role: ADMIN, BUILDER, or ADVISOR")

class UserRoleUpdate(BaseModel):
    role: str = Field(..., description="Platform role: ADMIN, BUILDER, or ADVISOR")

class RoleDefinitionResponse(BaseModel):
    id: str
    role_id: int
    name: str
    permittedActions: str
    accessBoundary: str
    status: str
    description: str

class ProjectStatusUpdate(BaseModel):
    status: str = Field(..., description="Status: ACTIVE, DISABLED, ARCHIVED")
    reason: Optional[str] = "Administrative action"

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

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Privileged Administrator User Creation",
    description="Allows authorized Administrator to provision ADMIN, BUILDER, or ADVISOR accounts (DEF-35)."
)
def create_admin_user(
    payload: AdminUserCreate,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    from app.core.security import get_password_hash

    clean_email = payload.email.strip().lower()
    if len(payload.password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    existing = db.query(User).filter(User.email == clean_email).first()
    if existing:
        raise ConflictError(f"User with email '{clean_email}' already exists.")

    target_role = payload.role.strip().upper()
    role_rec = db.query(Role).filter(Role.role_name.ilike(target_role)).first()
    if not role_rec:
        raise ValidationError(f"Invalid role '{payload.role}'. Must be ADMIN, BUILDER, or ADVISOR.")

    now = datetime.now(timezone.utc)
    new_user = User(
        email=clean_email,
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role_id=role_rec.role_id,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db.add(new_user)
    db.flush()

    if target_role == "ADVISOR":
        adv_prof = AdvisorProfile(
            user_id=new_user.user_id,
            organization_name=f"{new_user.full_name} Advisory",
            professional_title="Regulatory & Compliance Advisor",
            specialization="Financial Crime Compliance & Regulatory Strategy",
            bio=f"Verified compliance advisor {new_user.full_name}.",
            created_at=now,
            updated_at=now
        )
        db.add(adv_prof)
        db.flush()

    log_audit_event(
        db=db,
        project_id=1,
        actor_user_id=current_user.user_id,
        event_type="ADMIN_USER_CREATED",
        entity_type="USER",
        entity_id=new_user.user_id,
        event_description=f"Administrator '{current_user.full_name}' provisioned user '{new_user.email}' with role '{target_role}'",
        new_values={"email": new_user.email, "role": target_role, "is_active": True}
    )

    db.commit()
    db.refresh(new_user)

    return UserResponse(
        user_id=new_user.user_id,
        full_name=new_user.full_name,
        email=new_user.email,
        is_active=new_user.is_active,
        platform_role=role_rec.role_name,
        created_at=new_user.created_at,
        updated_at=new_user.updated_at
    )

@router.patch(
    "/users/{userId}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Account Status",
    description="Activates or deactivates a user account with session revocation (DEF-36)."
)
def update_user_status(
    userId: Union[int, str],
    payload: UserStatusUpdate,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    target_id = None
    if isinstance(userId, int) or (isinstance(userId, str) and str(userId).isdigit()):
        target_id = int(userId)
    elif isinstance(userId, str) and "USR-" in userId.upper():
        digits = "".join(filter(str.isdigit, userId))
        if digits:
            target_id = int(digits)

    user = None
    if target_id is not None:
        user = db.query(User).filter(User.user_id == target_id).first()
    if not user:
        user = db.query(User).filter(User.email.ilike(str(userId).strip())).first()

    if not user:
        raise NotFoundError("User", userId)

    # Prevent admin from deactivating self
    if user.user_id == current_user.user_id and not payload.is_active:
        raise ValidationError("Administrator cannot deactivate their own account.")

    old_status = user.is_active
    user.is_active = payload.is_active
    user.updated_at = datetime.now(timezone.utc)

    # Invalidate active user tokens immediately upon deactivation (DEF-36)
    if not payload.is_active:
        rev_entry = RevokedToken(
            jti=f"deact-{user.user_id}-{uuid.uuid4().hex[:8]}",
            token_signature=f"user-deactivated-{user.user_id}-{uuid.uuid4().hex[:12]}",
            revoked_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(rev_entry)

    db.commit()
    db.refresh(user)

    # Log audit event
    log_audit_event(
        db=db,
        project_id=1,
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

@router.get(
    "/roles",
    response_model=List[RoleDefinitionResponse],
    status_code=status.HTTP_200_OK,
    summary="List Platform Roles & Permissions",
    description="Returns platform role definitions and access boundaries (DEF-37)."
)
def list_admin_roles(
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    roles = db.query(Role).order_by(Role.role_id.asc()).all()
    ROLE_ACTION_MAP = {
        "ADMIN": "Full platform administration, user provisioning, project oversight, and immutable audit review.",
        "BUILDER": "Create and manage compliance projects, configure regulatory workflows, and invite advisors.",
        "ADVISOR": "Access invited project workspaces, review requirements, and submit defensible professional advice."
    }
    ROLE_BOUNDARY_MAP = {
        "ADMIN": "Global platform administration; project data isolation enforced; no automatic bypass of project ownership.",
        "BUILDER": "Tenant isolation enforced; restricted to own created and member projects.",
        "ADVISOR": "Project advice boundary enforced; access scoped to invited projects only."
    }

    results = []
    for r in roles:
        r_name = r.role_name.upper()
        results.append(RoleDefinitionResponse(
            id=f"ROLE-{str(r.role_id).zfill(3)}",
            role_id=r.role_id,
            name=r.role_name,
            permittedActions=ROLE_ACTION_MAP.get(r_name, r.description or "Standard platform permissions."),
            accessBoundary=ROLE_BOUNDARY_MAP.get(r_name, "Standard role boundary enforced."),
            status="Active definition",
            description=r.description or ""
        ))
    return results

@router.patch(
    "/users/{userId}/role",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Reassign User Platform Role",
    description="Updates user platform role with audit logging (DEF-37)."
)
def update_user_role(
    userId: Union[int, str],
    payload: UserRoleUpdate,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    target_id = None
    if isinstance(userId, int) or (isinstance(userId, str) and str(userId).isdigit()):
        target_id = int(userId)
    elif isinstance(userId, str) and "USR-" in userId.upper():
        digits = "".join(filter(str.isdigit, userId))
        if digits:
            target_id = int(digits)

    user = None
    if target_id is not None:
        user = db.query(User).filter(User.user_id == target_id).first()
    if not user:
        user = db.query(User).filter(User.email.ilike(str(userId).strip())).first()

    if not user:
        raise NotFoundError("User", userId)

    new_role_name = payload.role.strip().upper()
    role_rec = db.query(Role).filter(Role.role_name.ilike(new_role_name)).first()
    if not role_rec:
        raise ValidationError(f"Invalid role '{payload.role}'. Must be ADMIN, BUILDER, or ADVISOR.")

    old_role_name = user.role.role_name if user.role else "USER"
    user.role_id = role_rec.role_id
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    log_audit_event(
        db=db,
        project_id=1,
        actor_user_id=current_user.user_id,
        event_type="USER_ROLE_CHANGED",
        entity_type="USER",
        entity_id=user.user_id,
        event_description=f"Administrator '{current_user.full_name}' changed role of user '{user.email}' from '{old_role_name}' to '{new_role_name}'",
        old_values={"role": old_role_name},
        new_values={"role": new_role_name}
    )

    return UserResponse(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        platform_role=role_rec.role_name,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.patch(
    "/projects/{projectId}/status",
    status_code=status.HTTP_200_OK,
    summary="Update Project Status (Disable / Enable)",
    description="Enables, disables, or archives a project with audit logging (DEF-38)."
)
def update_project_status(
    projectId: Union[int, str],
    payload: ProjectStatusUpdate,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    from app.services.project_service import get_project_by_id
    project = get_project_by_id(db, projectId)
    raw_status = payload.status.strip().upper()
    if raw_status not in ("ACTIVE", "DISABLED", "ARCHIVED"):
        raise ValidationError("Project status must be ACTIVE, DISABLED, or ARCHIVED.")

    # Canonical status in PostgreSQL projects table (enforces chk_projects_status)
    db_status = "ARCHIVED" if raw_status in ("DISABLED", "ARCHIVED") else "ACTIVE"
    old_status = project.status
    project.status = db_status
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)

    log_audit_event(
        db=db,
        project_id=project.project_id,
        actor_user_id=current_user.user_id,
        event_type="PROJECT_STATUS_UPDATED",
        entity_type="PROJECT",
        entity_id=project.project_id,
        event_description=f"Project '{project.project_code}' status updated from '{old_status}' to '{raw_status}' by Admin '{current_user.full_name}'. Reason: {payload.reason}",
        old_values={"status": old_status},
        new_values={"status": raw_status, "db_status": db_status, "reason": payload.reason}
    )

    return {
        "project_id": project.project_id,
        "project_code": project.project_code,
        "status": raw_status,
        "db_status": project.status,
        "message": f"Project '{project.project_code}' successfully updated to status '{raw_status}'."
    }

@router.post(
    "/projects/{projectId}/disable",
    status_code=status.HTTP_200_OK,
    summary="Disable Project",
    description="Disables a project preventing further activity (DEF-38)."
)
def disable_project(
    projectId: Union[int, str],
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return update_project_status(
        projectId=projectId,
        payload=ProjectStatusUpdate(status="DISABLED", reason="Administrative project oversight disable action"),
        current_user=current_user,
        db=db
    )

@router.post(
    "/projects/{projectId}/activate",
    status_code=status.HTTP_200_OK,
    summary="Activate Project",
    description="Activates a project allowing project activity (DEF-38)."
)
def activate_project(
    projectId: Union[int, str],
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return update_project_status(
        projectId=projectId,
        payload=ProjectStatusUpdate(status="ACTIVE", reason="Administrative project oversight activate action"),
        current_user=current_user,
        db=db
    )

@router.get(
    "/advisor-invitations",
    status_code=status.HTTP_200_OK,
    summary="List All Advisor Invitations for Admin Oversight",
    description="Returns platform-wide advisor invitations formatted for Admin Monitoring (DEF-34)."
)
def list_admin_advisor_invitations(
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    invitations = db.query(AdvisorInvitation).order_by(AdvisorInvitation.created_at.desc()).all()
    results = []
    for inv in invitations:
        proj = db.query(Project).filter(Project.project_id == inv.project_id).first()
        inviter = db.query(User).filter(User.user_id == inv.invited_by).first()

        target_usr = db.query(User).filter(User.email.ilike(inv.advisor_email)).first()
        expertise = "Regulatory Compliance"
        if target_usr:
            prof = db.query(AdvisorProfile).filter(AdvisorProfile.user_id == target_usr.user_id).first()
            if prof and prof.specialization:
                expertise = prof.specialization

        status_str = inv.invitation_status.capitalize() if inv.invitation_status else "Pending"
        badge_class = "bg-[#12281b] border-emerald-800/50 text-emerald-400" if status_str == "Accepted" else "bg-[#281d11] border-amber-800/50 text-amber-400"
        dot_class = "bg-emerald-400" if status_str == "Accepted" else "bg-amber-400"

        results.append({
            "id": f"INV-{str(inv.invitation_id).zfill(3)}",
            "invitation_id": inv.invitation_id,
            "project": proj.project_code if proj else f"PRJ-{inv.project_id}",
            "projectName": proj.project_name if proj else "Unknown Project",
            "invitingBuilder": inviter.full_name if inviter else "Builder",
            "invitedAdvisor": target_usr.full_name if target_usr else inv.advisor_email,
            "advisorEmail": inv.advisor_email,
            "expertise": expertise,
            "invitationDate": inv.created_at.strftime("%d %b %Y") if inv.created_at else "Recently",
            "status": status_str,
            "statusBadgeClass": badge_class,
            "statusDotClass": dot_class,
            "accessStatus": "Active" if status_str == "Accepted" else "Pending Acceptance"
        })
    return results

@router.get(
    "/audit-events",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Platform Audit Events",
    description="Returns platform-wide immutable audit trail for administrators. Restricted to ADMIN."
)
@router.get(
    "/audit-logs",
    response_model=List[AuditEventResponse],
    status_code=status.HTTP_200_OK,
    summary="List Platform Audit Events (Alias)",
    description="Alias endpoint for admin audit logs (DEF-31)."
)
def list_admin_audit_events(
    limit: int = 100,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    events = list_all_audit_events(db=db, limit=limit)
    results = []
    for e in events:
        actor_name = e.actor.full_name if e.actor else "System"
        actor_role = e.actor.role.role_name if (e.actor and e.actor.role) else "Platform"
        project_code = e.project.project_code if e.project else None
        results.append(AuditEventResponse(
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
        ))
    return results
