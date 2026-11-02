from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.user import CurrentUserContext, UserMembershipContext, UserUpdateRequest
from app.schemas.advisor import AdvisorInboxInvitation
from app.security.authentication import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

def _build_user_context(user: User, db: Session) -> CurrentUserContext:
    memberships = (
        db.query(ProjectMember)
        .filter(ProjectMember.user_id == user.user_id, ProjectMember.member_status == "ACTIVE")
        .all()
    )

    membership_contexts = [
        UserMembershipContext(
            project_id=m.project_id,
            project_name=m.project.project_name if m.project else "Unknown",
            project_code=m.project.project_code if m.project else "",
            service_role=m.service_role,
            service_scope=m.service_scope,
            member_status=m.member_status
        )
        for m in memberships
    ]

    return CurrentUserContext(
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        platform_role=user.role.role_name.upper() if (user.role and user.role.role_name) else ("ADVISOR" if user.advisor_profile else "BUILDER"),
        memberships=membership_contexts
    )

@router.get(
    "/me",
    response_model=CurrentUserContext,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile & Context",
    description="Returns the authenticated user's profile, platform role, and active project memberships with service roles and scopes."
)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_user_context(current_user, db)

@router.patch(
    "/me",
    response_model=CurrentUserContext,
    status_code=status.HTTP_200_OK,
    summary="Update Current User Profile",
    description="Updates editable profile fields (such as full_name) for the authenticated user."
)
def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.full_name is not None and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

    return _build_user_context(current_user, db)

@router.get(
    "/me/invitations",
    response_model=List[AdvisorInboxInvitation],
    status_code=status.HTTP_200_OK,
    summary="Get Current User Advisory Invitations",
    description="Returns all active and pending invitations addressed to the authenticated advisor (DEF-34)."
)
def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.advisor import AdvisorInvitation
    from app.models.project import Project

    invitations = (
        db.query(AdvisorInvitation)
        .filter(AdvisorInvitation.advisor_email.ilike(current_user.email.strip()))
        .order_by(AdvisorInvitation.created_at.desc())
        .all()
    )

    results = []
    for inv in invitations:
        proj = db.query(Project).filter(Project.project_id == inv.project_id).first()
        inviter = db.query(User).filter(User.user_id == inv.invited_by).first()
        results.append(AdvisorInboxInvitation(
            invitation_id=inv.invitation_id,
            project_id=inv.project_id,
            project_code=proj.project_code if proj else f"PRJ-{inv.project_id}",
            project_name=proj.project_name if proj else f"Project {inv.project_id}",
            inviting_user=inviter.full_name if inviter else "Builder",
            access_level=inv.access_level,
            status=inv.invitation_status,
            invitation_token=inv.invitation_token,
            expires_at=inv.expires_at,
            created_at=inv.created_at
        ))
    return results

@router.get(
    "/me/notifications",
    status_code=status.HTTP_200_OK,
    summary="Get User Notifications",
    description="Returns real activity notifications and workflow invitations for the authenticated user."
)
def get_user_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.advisor import AdvisorInvitation
    from app.models.audit import AuditEvent
    from app.models.project import Project, ProjectMember

    notifications = []

    # 1. Any invitations for this user's email
    invitations = db.query(AdvisorInvitation).filter(
        AdvisorInvitation.advisor_email.ilike(current_user.email.strip())
    ).order_by(AdvisorInvitation.created_at.desc()).limit(10).all()

    for inv in invitations:
        proj = db.query(Project).filter(Project.project_id == inv.project_id).first()
        proj_name = proj.project_name if proj else f"Project {inv.project_id}"
        notifications.append({
            "id": f"inv-{inv.invitation_id}",
            "invitation_id": inv.invitation_id,
            "type": "INVITATION",
            "title": f"Advisory Invitation: {proj_name}",
            "message": f"You were invited to project '{proj_name}' with {inv.access_level} access.",
            "project_name": proj_name,
            "access_level": inv.access_level,
            "status": inv.invitation_status,
            "project_id": inv.project_id,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "is_read": inv.invitation_status != "PENDING"
        })

    # 2. Recent audit events for projects the user belongs to
    member_projects = db.query(ProjectMember.project_id).filter(
        ProjectMember.user_id == current_user.user_id
    ).all()
    project_ids = [p[0] for p in member_projects]

    if project_ids:
        recent_events = db.query(AuditEvent).filter(
            AuditEvent.project_id.in_(project_ids)
        ).order_by(AuditEvent.created_at.desc()).limit(15).all()

        for ev in recent_events:
            notifications.append({
                "id": f"evt-{ev.audit_event_id}",
                "type": ev.event_type,
                "title": ev.event_type.replace("_", " ").title(),
                "message": ev.event_description,
                "project_id": ev.project_id,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "is_read": False
            })

    return notifications

