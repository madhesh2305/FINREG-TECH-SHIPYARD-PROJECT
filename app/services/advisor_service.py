import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.identity import User, Role
from app.models.advisor import AdvisorProfile, AdvisorInvitation
from app.models.project import ProjectMember
from app.schemas.advisor import AdvisorInvitationCreate
from app.schemas.member import ROLE_TO_DEFAULT_SCOPE
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

def list_advisors(db: Session) -> List[AdvisorProfile]:
    # Ensure any active user with ADVISOR role has an AdvisorProfile (DEF-25)
    advisor_roles = db.query(Role).filter(Role.role_name.ilike("ADVISOR")).all()
    role_ids = [r.role_id for r in advisor_roles]
    if role_ids:
        advisor_users = (
            db.query(User)
            .filter(User.role_id.in_(role_ids), User.is_active == True)
            .all()
        )
        created_any = False
        for u in advisor_users:
            prof = db.query(AdvisorProfile).filter(AdvisorProfile.user_id == u.user_id).first()
            if not prof:
                now = datetime.now(timezone.utc)
                new_prof = AdvisorProfile(
                    user_id=u.user_id,
                    organization_name=f"{u.full_name} Advisory",
                    professional_title="Regulatory & Compliance Advisor",
                    specialization="Financial Crime Compliance & Regulatory Strategy",
                    bio=f"Verified compliance advisor {u.full_name}.",
                    created_at=u.created_at or now,
                    updated_at=u.updated_at or now,
                )
                db.add(new_prof)
                created_any = True
        if created_any:
            db.commit()

    return (
        db.query(AdvisorProfile)
        .join(User, User.user_id == AdvisorProfile.user_id)
        .join(Role, Role.role_id == User.role_id)
        .filter(Role.role_name.ilike("ADVISOR"), User.is_active == True)
        .order_by(AdvisorProfile.created_at.desc())
        .all()
    )

def get_advisor_by_id(db: Session, advisor_id: int) -> AdvisorProfile:
    advisor = db.query(AdvisorProfile).filter(AdvisorProfile.advisor_profile_id == advisor_id).first()
    if not advisor:
        raise NotFoundError(f"Advisor with ID {advisor_id} not found")
    return advisor

def create_advisor_invitation(db: Session, project_id: int, request: AdvisorInvitationCreate, actor: User) -> AdvisorInvitation:
    # Check if there is an active pending invitation
    existing = db.query(AdvisorInvitation).filter(
        AdvisorInvitation.project_id == project_id,
        AdvisorInvitation.advisor_email == request.advisor_email,
        AdvisorInvitation.invitation_status == "PENDING"
    ).first()

    if existing:
        raise ConflictError(f"A pending invitation already exists for {request.advisor_email}")

    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(32)
    expires_at = now + timedelta(days=request.expiry_days)

    raw_access = (request.access_level or "REGULATORY").upper().strip()
    if raw_access not in ("OWNER", "LEGAL", "REGULATORY", "TECH", "FUNDING_BUSINESS", "MARKETING"):
        if "LEGAL" in raw_access: canonical_access = "LEGAL"
        elif "TECH" in raw_access: canonical_access = "TECH"
        elif "FUNDING" in raw_access or "BUSINESS" in raw_access: canonical_access = "FUNDING_BUSINESS"
        elif "MARKETING" in raw_access: canonical_access = "MARKETING"
        else: canonical_access = "REGULATORY"
    else:
        canonical_access = raw_access

    invitation = AdvisorInvitation(
        project_id=project_id,
        invited_by=actor.user_id,
        advisor_email=request.advisor_email,
        access_level=canonical_access,
        invitation_status="PENDING",
        invitation_token=token,
        expires_at=expires_at,
        created_at=now
    )
    db.add(invitation)
    db.flush()

    # Automatically activate/create project membership for the invited advisor
    target_user = db.query(User).filter(User.email.ilike(request.advisor_email.strip())).first()
    if target_user:
        existing_mem = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.user_id
        ).first()
        if existing_mem:
            existing_mem.member_status = "ACTIVE"
            existing_mem.service_role = canonical_access
            existing_mem.service_scope = ROLE_TO_DEFAULT_SCOPE.get(canonical_access, "REGULATORY_ADVICE_SUPPORT")
            existing_mem.joined_at = now
        else:
            db.add(ProjectMember(
                project_id=project_id,
                user_id=target_user.user_id,
                service_role=canonical_access,
                service_scope=ROLE_TO_DEFAULT_SCOPE.get(canonical_access, "REGULATORY_ADVICE_SUPPORT"),
                member_status="ACTIVE",
                joined_at=now
            ))
        db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVISOR_INVITED",
        entity_type="ADVISOR_INVITATION",
        entity_id=invitation.invitation_id,
        event_description=f"Advisor invitation sent to {request.advisor_email} with access {request.access_level}",
        new_values={
            "advisor_email": invitation.advisor_email,
            "access_level": invitation.access_level,
            "expires_at": str(invitation.expires_at)
        }
    )

    db.commit()
    db.refresh(invitation)
    return invitation

def list_advisor_invitations(db: Session, project_id: int) -> List[AdvisorInvitation]:
    return (
        db.query(AdvisorInvitation)
        .filter(AdvisorInvitation.project_id == project_id)
        .order_by(AdvisorInvitation.created_at.desc())
        .all()
    )

def resend_advisor_invitation(db: Session, project_id: int, invitation_id: int, actor: User) -> AdvisorInvitation:
    invitation = db.query(AdvisorInvitation).filter(AdvisorInvitation.invitation_id == invitation_id).first()
    if not invitation:
        raise NotFoundError(f"Invitation with ID {invitation_id} not found")

    verify_object_belongs_to_project(invitation.project_id, project_id, "Invitation")

    if invitation.invitation_status != "PENDING":
        raise ValidationError(f"Cannot resend invitation with status: {invitation.invitation_status}")

    invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    invitation.invitation_token = secrets.token_urlsafe(32)

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVISOR_INVITATION_RESENT",
        entity_type="ADVISOR_INVITATION",
        entity_id=invitation.invitation_id,
        event_description=f"Invitation for {invitation.advisor_email} refreshed and resent",
    )

    db.commit()
    db.refresh(invitation)
    return invitation

def revoke_advisor_invitation(db: Session, project_id: int, invitation_id: int, actor: User) -> AdvisorInvitation:
    invitation = db.query(AdvisorInvitation).filter(AdvisorInvitation.invitation_id == invitation_id).first()
    if not invitation:
        raise NotFoundError(f"Invitation with ID {invitation_id} not found")

    verify_object_belongs_to_project(invitation.project_id, project_id, "Invitation")

    if invitation.invitation_status == "REVOKED":
        raise ConflictError("Invitation is already revoked")

    old_status = invitation.invitation_status
    invitation.invitation_status = "REVOKED"
    invitation.revoked_at = datetime.now(timezone.utc)

    # Revoke project membership for the advisor
    target_user = db.query(User).filter(User.email.ilike(invitation.advisor_email.strip())).first()
    if target_user:
        existing_mem = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.user_id
        ).first()
        if existing_mem:
            existing_mem.member_status = "REVOKED"
            db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVISOR_INVITATION_REVOKED",
        entity_type="ADVISOR_INVITATION",
        entity_id=invitation.invitation_id,
        event_description=f"Invitation for {invitation.advisor_email} revoked by {actor.full_name}",
        old_values={"invitation_status": old_status},
        new_values={"invitation_status": "REVOKED"}
    )

    db.commit()
    db.refresh(invitation)
    return invitation

def accept_advisor_invitation(db: Session, project_id: int, invitation_id: int, actor: User) -> AdvisorInvitation:
    invitation = db.query(AdvisorInvitation).filter(AdvisorInvitation.invitation_id == invitation_id).first()
    if not invitation:
        raise NotFoundError(f"Invitation with ID {invitation_id} not found")

    verify_object_belongs_to_project(invitation.project_id, project_id, "Invitation")

    if invitation.invitation_status != "PENDING":
        raise ConflictError(f"Invitation is already {invitation.invitation_status}")

    now = datetime.now(timezone.utc)
    invitation.invitation_status = "ACCEPTED"
    invitation.accepted_at = now

    # Find the user matching advisor_email
    target_user = db.query(User).filter(User.email.ilike(invitation.advisor_email)).first()
    if target_user:
        existing_mem = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.user_id
        ).first()
        if existing_mem:
            existing_mem.member_status = "ACTIVE"
            existing_mem.service_role = invitation.access_level
            existing_mem.service_scope = ROLE_TO_DEFAULT_SCOPE.get(invitation.access_level, "REGULATORY_ADVICE_SUPPORT")
            existing_mem.joined_at = now
        else:
            db.add(ProjectMember(
                project_id=project_id,
                user_id=target_user.user_id,
                service_role=invitation.access_level,
                service_scope=ROLE_TO_DEFAULT_SCOPE.get(invitation.access_level, "REGULATORY_ADVICE_SUPPORT"),
                member_status="ACTIVE",
                joined_at=now
            ))
        db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVISOR_ACCEPTED",
        entity_type="ADVISOR_INVITATION",
        entity_id=invitation.invitation_id,
        event_description=f"Advisor invitation accepted for {invitation.advisor_email}",
        new_values={"invitation_status": "ACCEPTED", "accepted_at": str(now)}
    )

    db.commit()
    db.refresh(invitation)
    return invitation
