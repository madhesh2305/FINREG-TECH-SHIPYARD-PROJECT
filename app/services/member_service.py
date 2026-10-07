from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.member import MemberCreate, MemberUpdate, ROLE_TO_DEFAULT_SCOPE, VALID_SERVICE_ROLES
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

def list_project_members(db: Session, project_id: int) -> List[ProjectMember]:
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.member_status == "ACTIVE")
        .all()
    )

def add_project_member(db: Session, project_id: int, request: MemberCreate, actor: User) -> ProjectMember:
    # Validate service role
    if request.service_role not in VALID_SERVICE_ROLES:
        raise ValidationError(f"Invalid service role. Allowed roles: {', '.join(VALID_SERVICE_ROLES)}")

    # Ensure target user exists
    target_user = db.query(User).filter(User.user_id == request.user_id).first()
    if not target_user:
        raise NotFoundError(f"User with ID {request.user_id} not found")

    # Platform role constraint: ADVISOR cannot be assigned OWNER
    if target_user.role and target_user.role.role_name == "ADVISOR" and request.service_role == "OWNER":
        raise ForbiddenError("Platform ADVISOR cannot be assigned the project OWNER role")

    # Determine canonical scope
    service_scope = request.service_scope or ROLE_TO_DEFAULT_SCOPE.get(request.service_role, "PROJECT_SUPPORT")

    # Check for existing membership
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == request.user_id
    ).first()

    if existing:
        if existing.member_status == "ACTIVE":
            raise ConflictError("User is already an active member of this project")
        # Reactivate existing revoked member
        old_status = existing.member_status
        existing.member_status = "ACTIVE"
        existing.service_role = request.service_role
        existing.service_scope = service_scope
        existing.joined_at = datetime.now(timezone.utc)
        member = existing
    else:
        member = ProjectMember(
            project_id=project_id,
            user_id=request.user_id,
            service_role=request.service_role,
            service_scope=service_scope,
            member_status="ACTIVE",
            joined_at=datetime.now(timezone.utc)
        )
        db.add(member)

    db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="MEMBER_ADDED",
        entity_type="PROJECT_MEMBER",
        entity_id=member.project_member_id,
        event_description=f"User '{target_user.full_name}' assigned role {member.service_role} by {actor.full_name}",
        new_values={
            "user_id": member.user_id,
            "service_role": member.service_role,
            "service_scope": member.service_scope,
            "member_status": member.member_status
        }
    )

    db.commit()
    db.refresh(member)
    return member

def update_project_member(db: Session, project_id: int, member_id: int, request: MemberUpdate, actor: User) -> ProjectMember:
    member = db.query(ProjectMember).filter(ProjectMember.project_member_id == member_id).first()
    if not member:
        raise NotFoundError(f"Project member with ID {member_id} not found")

    # BOLA / IDOR defense: Object must belong to route project_id
    verify_object_belongs_to_project(member.project_id, project_id, "Project member")

    old_values = {
        "service_role": member.service_role,
        "service_scope": member.service_scope,
        "member_status": member.member_status
    }

    if request.service_role is not None:
        if request.service_role not in VALID_SERVICE_ROLES:
            raise ValidationError(f"Invalid service role: {request.service_role}")
        member.service_role = request.service_role
        if request.service_scope is None:
            member.service_scope = ROLE_TO_DEFAULT_SCOPE.get(request.service_role, member.service_scope)

    if request.service_scope is not None:
        member.service_scope = request.service_scope

    if request.member_status is not None:
        member.member_status = request.member_status

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="MEMBER_UPDATED",
        entity_type="PROJECT_MEMBER",
        entity_id=member.project_member_id,
        event_description=f"Project member {member.user_id} updated by {actor.full_name}",
        old_values=old_values,
        new_values={
            "service_role": member.service_role,
            "service_scope": member.service_scope,
            "member_status": member.member_status
        }
    )

    db.commit()
    db.refresh(member)
    return member

def revoke_project_member(db: Session, project_id: int, member_id: int, actor: User) -> ProjectMember:
    member = db.query(ProjectMember).filter(ProjectMember.project_member_id == member_id).first()
    if not member:
        raise NotFoundError(f"Project member with ID {member_id} not found")

    verify_object_belongs_to_project(member.project_id, project_id, "Project member")

    # Prevent owner from revoking themselves if they are the only owner
    if member.user_id == actor.user_id and member.service_role == "OWNER":
        owner_count = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.service_role == "OWNER",
            ProjectMember.member_status == "ACTIVE"
        ).count()
        if owner_count <= 1:
            raise ForbiddenError("Cannot revoke the sole project OWNER")

    old_status = member.member_status
    member.member_status = "REVOKED"

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="MEMBER_REVOKED",
        entity_type="PROJECT_MEMBER",
        entity_id=member.project_member_id,
        event_description=f"Project member {member.user_id} revoked by {actor.full_name}",
        old_values={"member_status": old_status},
        new_values={"member_status": "REVOKED"}
    )

    db.commit()
    db.refresh(member)
    return member
