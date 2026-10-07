from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.identity import User
from app.models.advisor import AdvisorProfile
from app.models.advice import Advice, AdviceSourceLink
from app.models.regulatory import RegulatorySource
from app.models.project import ProjectMember
from app.schemas.advice import (
    AdviceCreate,
    AdviceUpdate,
    AdviceResponse,
    AdviceSourceLinkResponse,
    STATUS_NORMALIZATION,
    STATUS_DISPLAY_MAP,
)
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

def _map_advice_to_response(advice: Advice, db: Session) -> AdviceResponse:
    advisor_profile = db.query(AdvisorProfile).filter(AdvisorProfile.advisor_profile_id == advice.advisor_profile_id).first()
    advisor_name = advisor_profile.user.full_name if advisor_profile and advisor_profile.user else None
    advisor_org = advisor_profile.organization_name if advisor_profile else None

    links = []
    for link in advice.source_links:
        src = db.query(RegulatorySource).filter(RegulatorySource.source_id == link.source_id).first()
        links.append(
            AdviceSourceLinkResponse(
                advice_source_link_id=link.advice_source_link_id,
                source_id=link.source_id,
                reference_note=link.reference_note,
                source_title=src.source_title if src else None,
                citation_reference=src.version_label if src else None,
                created_at=link.created_at,
            )
        )

    return AdviceResponse(
        advice_id=advice.advice_id,
        project_id=advice.project_id,
        advisor_profile_id=advice.advisor_profile_id,
        advisor_name=advisor_name,
        advisor_organization=advisor_org,
        title=advice.title,
        advice_text=advice.advice_text,
        recommendation=advice.recommendation,
        assumptions=advice.assumptions or "",
        advice_status=advice.advice_status,
        display_status=STATUS_DISPLAY_MAP.get(advice.advice_status, advice.advice_status),
        submitted_at=advice.submitted_at,
        updated_at=advice.updated_at,
        source_links=links,
    )

def submit_advice(db: Session, project_id: int, request: AdviceCreate, actor: User) -> AdviceResponse:
    """Submit formal advisory review for a project."""
    # Find or verify advisor profile
    profile = db.query(AdvisorProfile).filter(AdvisorProfile.user_id == actor.user_id).first()
    if not profile:
        if actor.role and actor.role.role_name == "ADVISOR":
            profile = AdvisorProfile(
                user_id=actor.user_id,
                organization_name="Independent Advisory",
                professional_title="Regulatory & Compliance Advisor",
                specialization="Financial Crime Compliance & Regulatory Strategy",
                bio="Independent regulatory and compliance specialist.",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            db.flush()
        else:
            raise ForbiddenError("Only registered advisors can submit regulatory advice")

    # Normalize status
    raw_status = (request.advice_status or "SUBMITTED").upper().strip()
    status_val = STATUS_NORMALIZATION.get(raw_status)
    if not status_val:
        raise ValidationError(f"Invalid advice status '{request.advice_status}'. Allowed: DRAFT, SUBMITTED, REVIEWED, ARCHIVED")

    now = datetime.now(timezone.utc)
    advice = Advice(
        project_id=project_id,
        advisor_profile_id=profile.advisor_profile_id,
        title=request.title.strip(),
        advice_text=request.advice_text.strip(),
        recommendation=request.recommendation.strip(),
        assumptions=request.assumptions.strip() if request.assumptions else "",
        advice_status=status_val,
        submitted_at=now,
        updated_at=now,
    )
    db.add(advice)
    db.flush()

    # Link sources if provided
    if request.source_links:
        for s_link in request.source_links:
            source = db.query(RegulatorySource).filter(RegulatorySource.source_id == s_link.source_id).first()
            if not source:
                raise NotFoundError(f"Regulatory source with ID {s_link.source_id} not found")
            link = AdviceSourceLink(
                advice_id=advice.advice_id,
                source_id=source.source_id,
                reference_note=s_link.reference_note.strip(),
                created_at=now,
            )
            db.add(link)

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVICE_SUBMITTED",
        entity_type="ADVICE",
        entity_id=advice.advice_id,
        event_description=f"Advice '{advice.title}' submitted by {actor.full_name}",
        new_values={
            "advice_id": advice.advice_id,
            "title": advice.title,
            "status": advice.advice_status,
            "recommendation": advice.recommendation,
        },
    )

    db.commit()
    db.refresh(advice)
    return _map_advice_to_response(advice, db)

def list_project_advice(db: Session, project_id: int, status_filter: Optional[str] = None) -> List[AdviceResponse]:
    """List all advice items for a given project."""
    query = db.query(Advice).filter(Advice.project_id == project_id)
    if status_filter:
        norm_status = STATUS_NORMALIZATION.get(status_filter.upper().strip(), status_filter.upper().strip())
        query = query.filter(Advice.advice_status == norm_status)
    advice_list = query.order_by(Advice.submitted_at.desc()).all()
    return [_map_advice_to_response(a, db) for a in advice_list]

def get_advice_by_id(db: Session, project_id: int, advice_id: int) -> AdviceResponse:
    """Retrieve a single advice item by ID with BOLA verification."""
    advice = db.query(Advice).filter(Advice.advice_id == advice_id).first()
    if not advice:
        raise NotFoundError(f"Advice with ID {advice_id} not found")
    verify_object_belongs_to_project(advice.project_id, project_id, "Advice")
    return _map_advice_to_response(advice, db)

def update_advice(db: Session, project_id: int, advice_id: int, request: AdviceUpdate, actor: User) -> AdviceResponse:
    """Update advice content or status (e.g. project owner accepts/reviews advice)."""
    advice = db.query(Advice).filter(Advice.advice_id == advice_id).first()
    if not advice:
        raise NotFoundError(f"Advice with ID {advice_id} not found")
    verify_object_belongs_to_project(advice.project_id, project_id, "Advice")

    old_status = advice.advice_status

    if request.title is not None:
        advice.title = request.title.strip()
    if request.advice_text is not None:
        advice.advice_text = request.advice_text.strip()
    if request.recommendation is not None:
        advice.recommendation = request.recommendation.strip()
    if request.assumptions is not None:
        advice.assumptions = request.assumptions.strip()
    if request.advice_status is not None:
        norm_status = STATUS_NORMALIZATION.get(request.advice_status.upper().strip())
        if not norm_status:
            raise ValidationError(f"Invalid status '{request.advice_status}'. Allowed: DRAFT, SUBMITTED, REVIEWED, ARCHIVED")
        advice.advice_status = norm_status

    advice.updated_at = datetime.now(timezone.utc)

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="ADVICE_UPDATED",
        entity_type="ADVICE",
        entity_id=advice.advice_id,
        event_description=f"Advice '{advice.title}' updated by {actor.full_name}",
        old_values={"status": old_status},
        new_values={"status": advice.advice_status},
    )

    db.commit()
    db.refresh(advice)
    return _map_advice_to_response(advice, db)
