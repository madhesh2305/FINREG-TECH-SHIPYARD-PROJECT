import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, NotFoundError, ValidationError, ForbiddenError
from app.models.identity import User, Role
from app.models.advisor import AdvisorProfile, AdvisorInvitation
from app.models.project import ProjectMember
from app.schemas.advisor import AdvisorInvitationCreate, AdvisorSelectionRequest
from app.schemas.member import ROLE_TO_DEFAULT_SCOPE
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

MAX_PROJECT_ADVISORS = 2


def _normalize_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_project_advisor_slot_summary(db: Session, project_id: int) -> Dict[str, object]:
    """
    Compute canonical advisor slot usage for a project.
    Policy: The 2-advisor limit counts BOTH active/accepted advisors AND
    non-expired PENDING invitations, deduplicated by canonical email so
    an accepted invitation and its active ProjectMember share one slot.
    """
    now = datetime.now(timezone.utc)

    active_members = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.member_status == "ACTIVE",
            ProjectMember.service_role != "OWNER",
        )
        .all()
    )
    active_member_emails: Set[str] = set()
    for mem in active_members:
        if mem.user and mem.user.email:
            active_member_emails.add(mem.user.email.strip().lower())
        else:
            active_member_emails.add(f"user:{mem.user_id}")

    invs = (
        db.query(AdvisorInvitation)
        .filter(
            AdvisorInvitation.project_id == project_id,
            AdvisorInvitation.invitation_status.in_(["PENDING", "ACCEPTED"]),
        )
        .all()
    )
    accepted_emails: Set[str] = set()
    pending_emails: Set[str] = set()
    for inv in invs:
        email = (inv.advisor_email or "").strip().lower()
        if not email:
            continue
        if inv.invitation_status == "ACCEPTED":
            accepted_emails.add(email)
        elif inv.invitation_status == "PENDING":
            exp = _normalize_utc(inv.expires_at)
            if exp is None or exp > now:
                pending_emails.add(email)

    active_advisors = active_member_emails | accepted_emails
    pending_only = pending_emails - active_advisors
    occupied = active_advisors | pending_only

    return {
        "max_advisors": MAX_PROJECT_ADVISORS,
        "counts_rule": "PENDING_AND_ACCEPTED",
        "active_advisors": len(active_advisors),
        "pending_invitations": len(pending_only),
        "occupied_slots": len(occupied),
        "remaining_slots": max(0, MAX_PROJECT_ADVISORS - len(occupied)),
        "occupied_emails": sorted(occupied),
    }


def assert_advisor_slot_available(db: Session, project_id: int, target_email: Optional[str] = None) -> None:
    summary = get_project_advisor_slot_summary(db, project_id)
    normalized = (target_email or "").strip().lower()
    occupied_emails = set(summary["occupied_emails"])
    if normalized and normalized in occupied_emails:
        return
    if int(summary["occupied_slots"]) >= MAX_PROJECT_ADVISORS:
        raise ConflictError(
            f"Advisor limit reached: projects support at most {MAX_PROJECT_ADVISORS} advisors "
            "(counting both pending invitations and accepted/active advisors)."
        )

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

    raw_profiles = (
        db.query(AdvisorProfile)
        .join(User, User.user_id == AdvisorProfile.user_id)
        .join(Role, Role.role_id == User.role_id)
        .filter(Role.role_name.ilike("ADVISOR"), User.is_active == True)
        .order_by(AdvisorProfile.created_at.desc())
        .all()
    )
    # Deduplicate by user_id to prevent duplicate advisor cards (UAT-DIR-01)
    seen_users = set()
    unique_profiles = []
    for p in raw_profiles:
        if p.user_id not in seen_users:
            seen_users.add(p.user_id)
            unique_profiles.append(p)
    return unique_profiles

def get_advisor_by_id(db: Session, advisor_id: int) -> AdvisorProfile:
    advisor = db.query(AdvisorProfile).filter(AdvisorProfile.advisor_profile_id == advisor_id).first()
    if not advisor:
        raise NotFoundError(f"Advisor with ID {advisor_id} not found")
    return advisor

def create_advisor_invitation(db: Session, project_id: int, request: AdvisorInvitationCreate, actor: User) -> AdvisorInvitation:
    from app.models.project import Project

    # Ensure project is active and not disabled (DEF-38)
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if project and project.status in ("DISABLED", "ARCHIVED"):
        raise ForbiddenError(f"Project '{project.project_code}' is disabled/archived and cannot issue advisor invitations.")

    clean_email = request.advisor_email.strip().lower()

    # Check if there is an active pending or accepted invitation (DEF-32)
    existing = db.query(AdvisorInvitation).filter(
        AdvisorInvitation.project_id == project_id,
        AdvisorInvitation.advisor_email.ilike(clean_email),
        AdvisorInvitation.invitation_status.in_(["PENDING", "ACCEPTED"])
    ).first()

    if existing:
        raise ConflictError(f"An active invitation already exists for {clean_email} in this project. Use resend if needed.")

    # Check if user is already an active project member (DEF-32)
    target_user = db.query(User).filter(User.email.ilike(clean_email)).first()
    if target_user:
        existing_mem = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.user_id,
            ProjectMember.member_status == "ACTIVE"
        ).first()
        if existing_mem:
            raise ConflictError(f"Advisor {clean_email} is already an active member of this project.")

    # Enforce 2-advisor limit (counts BOTH pending invitations and accepted/active advisors)
    assert_advisor_slot_available(db, project_id, target_email=clean_email)

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
        advisor_email=clean_email,
        access_level=canonical_access,
        invitation_status="PENDING",
        invitation_token=token,
        expires_at=expires_at,
        created_at=now
    )
    db.add(invitation)
    db.flush()

    # NOTE: Do NOT grant ProjectMember access upon invitation or expertise selection;
    # active membership is created ONLY after the advisor accepts the invitation.
    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVISOR_INVITED",
        entity_type="ADVISOR_INVITATION",
        entity_id=invitation.invitation_id,
        event_description=f"Advisor invitation sent to {clean_email} with access {canonical_access}",
        new_values={
            "advisor_email": invitation.advisor_email,
            "access_level": invitation.access_level,
            "invitation_status": "PENDING",
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

def _revoke_invitation_and_member(
    db: Session,
    project_id: int,
    invitation_id: int,
    actor: User,
    event_type: str,
    action_label: str,
) -> AdvisorInvitation:
    from app.models.project import Project

    project = db.query(Project).filter(Project.project_id == project_id).first()
    if project and project.status in ("DISABLED", "ARCHIVED"):
        raise ForbiddenError(f"Project '{project.project_code}' is disabled/archived and cannot modify invitations.")

    invitation = db.query(AdvisorInvitation).filter(AdvisorInvitation.invitation_id == invitation_id).first()
    if not invitation:
        raise NotFoundError(f"Invitation with ID {invitation_id} not found")

    verify_object_belongs_to_project(invitation.project_id, project_id, "Invitation")

    if invitation.invitation_status == "REVOKED":
        raise ConflictError("Invitation is already cancelled or revoked")

    now = datetime.now(timezone.utc)
    old_status = invitation.invitation_status
    invitation.invitation_status = "REVOKED"
    invitation.revoked_at = now

    # Revoke any matching ProjectMember rows so cancelled/revoked advisors never regain access on refresh
    target_user = db.query(User).filter(User.email.ilike(invitation.advisor_email.strip())).first()
    if target_user:
        matching_mems = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == target_user.user_id,
            ProjectMember.service_role != "OWNER",
        ).all()
        for existing_mem in matching_mems:
            existing_mem.member_status = "REVOKED"
        if matching_mems:
            db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type=event_type,
        entity_type="ADVISOR_INVITATION",
        entity_id=invitation.invitation_id,
        event_description=f"Advisor invitation for {invitation.advisor_email} {action_label} by {actor.full_name or actor.email}",
        old_values={"invitation_status": old_status},
        new_values={"invitation_status": "REVOKED", "revoked_at": now.isoformat()}
    )

    db.commit()
    db.refresh(invitation)
    return invitation


def revoke_advisor_invitation(db: Session, project_id: int, invitation_id: int, actor: User) -> AdvisorInvitation:
    return _revoke_invitation_and_member(
        db=db,
        project_id=project_id,
        invitation_id=invitation_id,
        actor=actor,
        event_type="ADVISOR_INVITATION_REVOKED",
        action_label="revoked",
    )


def cancel_advisor_invitation(db: Session, project_id: int, invitation_id: int, actor: User) -> AdvisorInvitation:
    """Withdraw or cancel an advisor invitation, revoke project access, and log an audit event (UAT-INV-02, UAT-AUD-01)."""
    return _revoke_invitation_and_member(
        db=db,
        project_id=project_id,
        invitation_id=invitation_id,
        actor=actor,
        event_type="ADVISOR_INVITATION_CANCELLED",
        action_label="cancelled",
    )


def accept_advisor_invitation(db: Session, project_id: int, invitation_id: int, actor: User) -> AdvisorInvitation:
    from app.models.project import Project

    project = db.query(Project).filter(Project.project_id == project_id).first()
    if project and project.status in ("DISABLED", "ARCHIVED"):
        raise ForbiddenError(f"Project '{project.project_code}' is disabled/archived and cannot accept invitations.")

    invitation = db.query(AdvisorInvitation).filter(AdvisorInvitation.invitation_id == invitation_id).first()
    if not invitation:
        raise NotFoundError(f"Invitation with ID {invitation_id} not found")

    verify_object_belongs_to_project(invitation.project_id, project_id, "Invitation")

    if invitation.advisor_email.strip().lower() != actor.email.strip().lower():
        raise ForbiddenError("Only the invited advisor may accept this invitation.")

    if invitation.invitation_status != "PENDING":
        raise ConflictError(f"Invitation is already {invitation.invitation_status}")

    now = datetime.now(timezone.utc)
    exp = _normalize_utc(invitation.expires_at)
    if exp is not None and exp < now:
        invitation.invitation_status = "EXPIRED"
        db.commit()
        raise ConflictError("Invitation has expired.")

    assert_advisor_slot_available(db, project_id, target_email=invitation.advisor_email)

    invitation.invitation_status = "ACCEPTED"
    invitation.accepted_at = now

    # Grant active project membership ONLY upon explicit invitation acceptance
    target_user = db.query(User).filter(User.email.ilike(invitation.advisor_email.strip())).first()
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
        old_values={"invitation_status": "PENDING"},
        new_values={"invitation_status": "ACCEPTED", "accepted_at": now.isoformat()}
    )

    db.commit()
    db.refresh(invitation)
    return invitation


def select_advisor_for_project(
    db: Session,
    project_id: int,
    request: AdvisorSelectionRequest,
    actor: User
) -> AdvisorInvitation:
    """Assign or invite an advisor directly during the advisor selection step (DEF-33)."""
    clean_email = None
    if request.advisor_email:
        clean_email = request.advisor_email.strip().lower()
    elif request.advisor_id:
        prof = db.query(AdvisorProfile).filter(AdvisorProfile.advisor_profile_id == request.advisor_id).first()
        if prof and prof.user:
            clean_email = prof.user.email.strip().lower()
        else:
            usr = db.query(User).filter(User.user_id == request.advisor_id).first()
            if usr:
                clean_email = usr.email.strip().lower()

    if not clean_email:
        raise ValidationError("Could not resolve valid advisor email or ID for selection.")

    invitation_payload = AdvisorInvitationCreate(
        advisor_email=clean_email,
        access_level=request.access_level,
        expiry_days=request.expiry_days
    )
    return create_advisor_invitation(db=db, project_id=project_id, request=invitation_payload, actor=actor)
