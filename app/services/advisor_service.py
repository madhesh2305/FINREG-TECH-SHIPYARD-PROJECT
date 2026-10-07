import secrets
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.advisor import AdvisorProfile, AdvisorInvitation
from app.schemas.advisor import AdvisorInvitationCreate
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

def list_advisors(db: Session) -> List[AdvisorProfile]:
    return db.query(AdvisorProfile).join(User, User.user_id == AdvisorProfile.user_id).all()

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

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=request.expiry_days)

    invitation = AdvisorInvitation(
        project_id=project_id,
        invited_by=actor.user_id,
        advisor_email=request.advisor_email,
        access_level=request.access_level,
        invitation_status="PENDING",
        invitation_token=token,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(invitation)
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
