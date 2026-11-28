from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.audit import AuditEvent
from app.models.identity import User
from app.models.project import Project, ProjectMember
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.schemas.regulatory import (
    RegulatoryRequirementCreate,
    RegulatoryRequirementResponse,
    RegulatoryRequirementUpdate,
    RegulatorySourceCreate,
    RegulatorySourceResponse,
    RegulatorySourceValidationRequest,
)
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project


def _normalize_tokens(value: Optional[str]) -> List[str]:
    if not value:
        return []
    raw = value.replace("/", ",").replace("|", ",").replace("&", ",").replace("(", ",").replace(")", ",")
    tokens = []
    aliases = {
        "united kingdom": "uk",
        "uk": "uk",
        "great britain": "uk",
        "gb": "uk",
        "european union": "eu",
        "eu": "eu",
        "united states": "us",
        "usa": "us",
        "us": "us",
        "singapore": "sg",
        "sg": "sg",
        "global": "global",
        "international": "global",
    }
    for part in raw.split(","):
        cleaned = " ".join(part.strip().lower().split())
        if not cleaned:
            continue
        tokens.append(aliases.get(cleaned, cleaned))
    return list(dict.fromkeys(tokens))


def jurisdictions_match(project_jurisdiction: Optional[str], source_jurisdiction: Optional[str]) -> bool:
    """Return True only when project and source jurisdictions share a specific canonical jurisdiction."""
    proj_tokens = set(_normalize_tokens(project_jurisdiction))
    src_tokens = set(_normalize_tokens(source_jurisdiction))
    if not proj_tokens or not src_tokens:
        return False
    return bool(proj_tokens & src_tokens)


def _get_source_lifecycle_map(db: Session, source_ids: List[int]) -> Dict[int, dict]:
    if not source_ids:
        return {}
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_type == "REGULATORY_SOURCE",
            AuditEvent.entity_id.in_(source_ids),
        )
        .order_by(AuditEvent.created_at.asc(), AuditEvent.audit_event_id.asc())
        .all()
    )
    lifecycle: Dict[int, dict] = {}
    for ev in events:
        if ev.entity_id is None:
            continue
        entry = lifecycle.setdefault(ev.entity_id, {})
        payload = ev.new_values or {}
        if ev.event_type == "SOURCE_CREATED":
            for k in ("source_code", "document_name", "provenance", "section_reference", "applicability_notes", "submitted_by_user_id", "submitted_by_name"):
                if payload.get(k) is not None:
                    entry[k] = payload[k]
            if payload.get("validation_state"):
                entry["validation_state"] = payload["validation_state"]
        elif ev.event_type in ("SOURCE_APPROVED", "SOURCE_VALIDATED", "SOURCE_REJECTED", "SOURCE_CHANGES_REQUESTED", "SOURCE_VALIDATION_UPDATED"):
            for k in ("validation_state", "reviewer_user_id", "reviewer_name", "reviewed_at", "decision"):
                if payload.get(k) is not None:
                    entry[k] = payload[k]
            if payload.get("reason") is not None:
                entry["review_reason"] = payload["reason"]
    return lifecycle


def serialize_regulatory_source(
    db: Session,
    source: RegulatorySource,
    lifecycle_map: Optional[Dict[int, dict]] = None,
) -> RegulatorySourceResponse:
    if lifecycle_map is None:
        lifecycle_map = _get_source_lifecycle_map(db, [source.source_id])
    meta = lifecycle_map.get(source.source_id, {})

    if source.validation_status == "VALIDATED":
        validation_state = "APPROVED"
    elif source.validation_status == "REJECTED":
        validation_state = "REJECTED"
    elif meta.get("validation_state") == "CHANGES_REQUESTED":
        validation_state = "CHANGES_REQUESTED"
    else:
        validation_state = "PENDING_VALIDATION"

    doc_name = meta.get("document_name")
    if not doc_name and source.source_url and source.source_url.startswith("document://"):
        doc_name = source.source_url[len("document://"):]

    reviewed_at_val = meta.get("reviewed_at")
    if isinstance(reviewed_at_val, str):
        try:
            reviewed_at_val = datetime.fromisoformat(reviewed_at_val)
        except ValueError:
            reviewed_at_val = None

    return RegulatorySourceResponse(
        source_id=source.source_id,
        source_title=source.source_title,
        issuing_authority=source.issuing_authority,
        jurisdiction=source.jurisdiction,
        source_url=source.source_url,
        version_label=source.version_label,
        publication_date=source.publication_date,
        validation_status=source.validation_status,
        topic=source.topic,
        relevance=source.relevance,
        applicability_rationale=source.applicability_rationale,
        retrieved_at=source.retrieved_at,
        created_at=source.created_at,
        updated_at=source.updated_at,
        source_code=meta.get("source_code") or f"SRC-{source.source_id:03d}",
        document_name=doc_name,
        provenance=meta.get("provenance") or f"{source.issuing_authority} | {source.jurisdiction} | {source.version_label}",
        section_reference=meta.get("section_reference"),
        applicability_notes=meta.get("applicability_notes") or source.applicability_rationale,
        validation_state=validation_state,
        submitted_by_user_id=meta.get("submitted_by_user_id"),
        submitted_by_name=meta.get("submitted_by_name"),
        reviewer_user_id=meta.get("reviewer_user_id"),
        reviewer_name=meta.get("reviewer_name"),
        reviewed_at=reviewed_at_val,
        decision=meta.get("decision") or (validation_state if validation_state != "PENDING_VALIDATION" else None),
        review_reason=meta.get("review_reason"),
    )


def serialize_regulatory_sources(db: Session, sources: List[RegulatorySource]) -> List[RegulatorySourceResponse]:
    if not sources:
        return []
    lifecycle_map = _get_source_lifecycle_map(db, [s.source_id for s in sources])
    return [serialize_regulatory_source(db, s, lifecycle_map=lifecycle_map) for s in sources]


def list_regulatory_sources(
    db: Session,
    jurisdiction: Optional[str] = None,
    topic: Optional[str] = None,
    search: Optional[str] = None,
    validation_state: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[RegulatorySourceResponse], int]:
    query = db.query(RegulatorySource)

    if jurisdiction:
        query = query.filter(RegulatorySource.jurisdiction.ilike(f"%{jurisdiction}%"))
    if topic:
        query = query.filter(RegulatorySource.topic.ilike(f"%{topic}%"))
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (RegulatorySource.source_title.ilike(pattern)) |
            (RegulatorySource.issuing_authority.ilike(pattern)) |
            (RegulatorySource.relevance.ilike(pattern))
        )

    ordered = query.order_by(RegulatorySource.updated_at.desc(), RegulatorySource.source_id.desc()).all()
    serialized = serialize_regulatory_sources(db, ordered)
    if validation_state:
        target = validation_state.upper().strip()
        serialized = [
            s for s in serialized
            if s.validation_state == target or s.validation_status == target
        ]

    total = len(serialized)
    start = (page - 1) * page_size
    items = serialized[start:start + page_size]
    return items, total


def get_regulatory_source_by_id(db: Session, source_id: int) -> RegulatorySourceResponse:
    source = db.query(RegulatorySource).filter(RegulatorySource.source_id == source_id).first()
    if not source:
        raise NotFoundError(f"Regulatory source with ID {source_id} not found")
    return serialize_regulatory_source(db, source)


def create_regulatory_source(db: Session, request: RegulatorySourceCreate, actor: User) -> RegulatorySourceResponse:
    clean_url = (request.source_url or "").strip()
    clean_doc = (request.document_name or "").strip()
    if not clean_url and not clean_doc:
        raise ValidationError("Either an official source_url or document_name must be provided for regulatory provenance.")

    effective_url = clean_url or f"document://{clean_doc}"
    now = datetime.now(timezone.utc)
    provenance = (request.provenance or "").strip() or (
        f"Submitted by {actor.full_name} ({actor.role.role_name if actor.role else 'USER'}) | "
        f"{request.issuing_authority} | {request.jurisdiction}"
    )

    # Registering a source ALWAYS enters PENDING / PENDING_VALIDATION and requires explicit ADMIN review
    source = RegulatorySource(
        source_title=request.source_title,
        issuing_authority=request.issuing_authority,
        jurisdiction=request.jurisdiction,
        source_url=effective_url,
        version_label=request.version_label,
        publication_date=request.publication_date,
        retrieved_at=now,
        validation_status="PENDING",
        topic=request.topic,
        relevance=request.relevance,
        applicability_rationale=request.applicability_notes or request.applicability_rationale,
        created_at=now,
        updated_at=now,
    )
    db.add(source)
    db.flush()

    source_code = f"SRC-{source.source_id:03d}"
    log_audit_event(
        db=db,
        project_id=None,
        actor_user_id=actor.user_id,
        event_type="SOURCE_CREATED",
        entity_type="REGULATORY_SOURCE",
        entity_id=source.source_id,
        event_description=f"Regulatory source '{source.source_title}' ({source_code}) submitted for validation by {actor.full_name}",
        new_values={
            "source_code": source_code,
            "source_title": source.source_title,
            "issuing_authority": source.issuing_authority,
            "jurisdiction": source.jurisdiction,
            "source_url": effective_url,
            "document_name": clean_doc or None,
            "version_label": source.version_label,
            "publication_date": str(source.publication_date),
            "topic": source.topic,
            "provenance": provenance,
            "section_reference": request.section_reference,
            "applicability_notes": request.applicability_notes or source.applicability_rationale,
            "validation_status": "PENDING",
            "validation_state": "PENDING_VALIDATION",
            "submitted_by_user_id": actor.user_id,
            "submitted_by_name": actor.full_name,
        },
    )

    db.commit()
    db.refresh(source)
    return serialize_regulatory_source(db, source)


def validate_regulatory_source(
    db: Session,
    source_id: int,
    request: RegulatorySourceValidationRequest,
    reviewer: User,
) -> RegulatorySourceResponse:
    role_name = reviewer.role.role_name.upper() if reviewer.role and reviewer.role.role_name else ""
    if role_name != "ADMIN":
        raise ForbiddenError("Only authorized ADMIN reviewers can validate, reject, or request changes on regulatory sources.")

    source = db.query(RegulatorySource).filter(RegulatorySource.source_id == source_id).first()
    if not source:
        raise NotFoundError(f"Regulatory source with ID {source_id} not found")

    previous = serialize_regulatory_source(db, source)
    raw_decision = request.decision.upper().strip()
    reason = (request.reason or "").strip()

    if raw_decision in ("APPROVED", "VALIDATED"):
        db_status = "VALIDATED"
        val_state = "APPROVED"
        canonical_decision = "APPROVED"
        event_type = "SOURCE_APPROVED"
        if not reason:
            reason = "Approved after regulatory provenance and official source validation."
    elif raw_decision == "REJECTED":
        if not reason:
            raise ValidationError("A detailed reason is required when rejecting a regulatory source.")
        db_status = "REJECTED"
        val_state = "REJECTED"
        canonical_decision = "REJECTED"
        event_type = "SOURCE_REJECTED"
    elif raw_decision == "CHANGES_REQUESTED":
        if not reason:
            raise ValidationError("A clear reason describing required revisions is required when requesting changes.")
        db_status = "PENDING"
        val_state = "CHANGES_REQUESTED"
        canonical_decision = "CHANGES_REQUESTED"
        event_type = "SOURCE_CHANGES_REQUESTED"
    else:
        raise ValidationError(f"Unsupported validation decision '{request.decision}'.")

    now = datetime.now(timezone.utc)
    source.validation_status = db_status
    source.updated_at = now

    log_audit_event(
        db=db,
        project_id=None,
        actor_user_id=reviewer.user_id,
        event_type=event_type,
        entity_type="REGULATORY_SOURCE",
        entity_id=source.source_id,
        event_description=f"Regulatory source '{source.source_title}' marked {val_state} by {reviewer.full_name}: {reason}",
        old_values={
            "validation_status": previous.validation_status,
            "validation_state": previous.validation_state,
        },
        new_values={
            "validation_status": db_status,
            "validation_state": val_state,
            "decision": canonical_decision,
            "reason": reason,
            "reviewer_user_id": reviewer.user_id,
            "reviewer_name": reviewer.full_name,
            "reviewed_at": now.isoformat(),
        },
    )

    db.commit()
    db.refresh(source)
    return serialize_regulatory_source(db, source)

def _get_requirement_audit_map(db: Session, requirement_ids: List[int]) -> Dict[int, dict]:
    if not requirement_ids:
        return {}
    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.entity_type == "REGULATORY_REQUIREMENT",
            AuditEvent.entity_id.in_(requirement_ids),
        )
        .order_by(AuditEvent.created_at.asc(), AuditEvent.audit_event_id.asc())
        .all()
    )
    req_meta: Dict[int, dict] = {}
    for ev in events:
        if ev.entity_id is None:
            continue
        entry = req_meta.setdefault(ev.entity_id, {})
        payload = ev.new_values or {}
        for k in ("section_reference", "source_version", "jurisdiction", "applicability_notes"):
            if payload.get(k) is not None:
                entry[k] = payload[k]
    return req_meta


def serialize_regulatory_requirements(
    db: Session,
    reqs: List[RegulatoryRequirement],
) -> List[RegulatoryRequirementResponse]:
    if not reqs:
        return []
    source_ids = list({r.source_id for r in reqs})
    project_ids = list({r.project_id for r in reqs})
    req_ids = [r.requirement_id for r in reqs]

    sources = db.query(RegulatorySource).filter(RegulatorySource.source_id.in_(source_ids)).all()
    lifecycle_map = _get_source_lifecycle_map(db, source_ids)
    source_resp_map = {
        s.source_id: serialize_regulatory_source(db, s, lifecycle_map=lifecycle_map)
        for s in sources
    }
    projects = db.query(Project).filter(Project.project_id.in_(project_ids)).all()
    project_map = {p.project_id: p for p in projects}
    req_audit_map = _get_requirement_audit_map(db, req_ids)

    results: List[RegulatoryRequirementResponse] = []
    for r in reqs:
        src_resp = source_resp_map.get(r.source_id)
        proj = project_map.get(r.project_id)
        rmeta = req_audit_map.get(r.requirement_id, {})
        section_ref = rmeta.get("section_reference") or (src_resp.section_reference if src_resp else None) or f"Ref: {r.requirement_code}"
        src_version = rmeta.get("source_version") or (src_resp.version_label if src_resp else None)
        jurisdiction_val = rmeta.get("jurisdiction") or (src_resp.jurisdiction if src_resp else None)
        app_notes = rmeta.get("applicability_notes") or (src_resp.applicability_notes if src_resp else None)

        results.append(
            RegulatoryRequirementResponse(
                requirement_id=r.requirement_id,
                project_id=r.project_id,
                source_id=r.source_id,
                requirement_code=r.requirement_code,
                requirement_title=r.requirement_title,
                requirement_text=r.requirement_text,
                applicability_status=r.applicability_status,
                requirement_status=r.requirement_status,
                created_at=r.created_at,
                updated_at=r.updated_at,
                source_code=src_resp.source_code if src_resp else f"SRC-{r.source_id:03d}",
                source_title=src_resp.source_title if src_resp else None,
                section_reference=section_ref,
                source_version=src_version,
                jurisdiction=jurisdiction_val,
                applicability_notes=app_notes,
                validation_state=src_resp.validation_state if src_resp else None,
                source_validation_status=src_resp.validation_status if src_resp else None,
                project_code=proj.project_code if proj else None,
                project_name=proj.project_name if proj else None,
                source=src_resp,
            )
        )
    return results


def serialize_regulatory_requirement(db: Session, req: RegulatoryRequirement) -> RegulatoryRequirementResponse:
    return serialize_regulatory_requirements(db, [req])[0]


def list_project_requirements(
    db: Session,
    project_id: int,
    status: Optional[str] = None,
    applicability: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    scope: Optional[str] = None,
) -> List[RegulatoryRequirementResponse]:
    query = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.project_id == project_id)

    if status:
        query = query.filter(RegulatoryRequirement.requirement_status == status)
    if applicability:
        query = query.filter(RegulatoryRequirement.applicability_status == applicability)

    reqs = query.order_by(RegulatoryRequirement.requirement_code.asc()).all()
    serialized = serialize_regulatory_requirements(db, reqs)

    if jurisdiction:
        serialized = [r for r in serialized if jurisdictions_match(jurisdiction, r.jurisdiction)]
    if scope:
        scope_l = scope.strip().lower()
        serialized = [
            r for r in serialized
            if (r.source and scope_l in (r.source.topic or "").lower())
            or scope_l in (r.requirement_title or "").lower()
            or scope_l in (r.requirement_text or "").lower()
        ]
    return serialized


def list_advisor_assigned_requirements(
    db: Session,
    user: User,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    applicability: Optional[str] = None,
    jurisdiction: Optional[str] = None,
) -> List[RegulatoryRequirementResponse]:
    """Return requirements ONLY for projects where the advisor has accepted/active membership."""
    from app.models.advisor import AdvisorInvitation

    active_member_pids = {
        row[0]
        for row in db.query(ProjectMember.project_id)
        .filter(
            ProjectMember.user_id == user.user_id,
            ProjectMember.member_status == "ACTIVE",
        )
        .all()
    }
    accepted_inv_pids = {
        row[0]
        for row in db.query(AdvisorInvitation.project_id)
        .filter(
            AdvisorInvitation.advisor_email.ilike(user.email.strip()),
            AdvisorInvitation.invitation_status == "ACCEPTED",
        )
        .all()
    }
    allowed_pids = active_member_pids | accepted_inv_pids

    if project_id is not None:
        if project_id not in allowed_pids:
            raise ForbiddenError("Advisor does not have accepted/active assignment for the requested project.")
        target_pids = [project_id]
    else:
        target_pids = list(allowed_pids)

    if not target_pids:
        return []

    query = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.project_id.in_(target_pids))
    if status:
        query = query.filter(RegulatoryRequirement.requirement_status == status)
    if applicability:
        query = query.filter(RegulatoryRequirement.applicability_status == applicability)

    reqs = query.order_by(RegulatoryRequirement.project_id.asc(), RegulatoryRequirement.requirement_code.asc()).all()
    serialized = serialize_regulatory_requirements(db, reqs)
    if jurisdiction:
        serialized = [r for r in serialized if jurisdictions_match(jurisdiction, r.jurisdiction)]
    return serialized


def get_project_requirement_by_id(db: Session, project_id: int, requirement_id: int) -> RegulatoryRequirementResponse:
    req = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.requirement_id == requirement_id).first()
    if not req:
        raise NotFoundError(f"Requirement with ID {requirement_id} not found")

    verify_object_belongs_to_project(req.project_id, project_id, "Requirement")
    return serialize_regulatory_requirement(db, req)


def create_project_requirement(
    db: Session,
    project_id: int,
    request: RegulatoryRequirementCreate,
    actor: User
) -> RegulatoryRequirementResponse:
    # 1. Provenance validation: Ensure source exists AND is APPROVED/VALIDATED
    source = db.query(RegulatorySource).filter(RegulatorySource.source_id == request.source_id).first()
    if not source:
        raise NotFoundError(f"Approved Regulatory Source with ID {request.source_id} does not exist")

    serialized_source = serialize_regulatory_source(db, source)
    if source.validation_status != "VALIDATED" or serialized_source.validation_state != "APPROVED":
        raise ValidationError(
            f"Regulatory Source {source.source_id} ('{source.source_title}') has status "
            f"'{serialized_source.validation_state}' and must be APPROVED/VALIDATED before creating requirements."
        )

    # 2. Check code uniqueness for project
    existing = db.query(RegulatoryRequirement).filter(
        RegulatoryRequirement.project_id == project_id,
        RegulatoryRequirement.requirement_code == request.requirement_code
    ).first()
    if existing:
        raise ConflictError(f"Requirement with code '{request.requirement_code}' already exists in this project")

    now = datetime.now(timezone.utc)
    req = RegulatoryRequirement(
        project_id=project_id,
        source_id=request.source_id,
        requirement_code=request.requirement_code,
        requirement_title=request.requirement_title,
        requirement_text=request.requirement_text,
        applicability_status=request.applicability_status,
        requirement_status=request.requirement_status,
        created_at=now,
        updated_at=now
    )
    db.add(req)
    db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="REQUIREMENT_PUBLISHED",
        entity_type="REGULATORY_REQUIREMENT",
        entity_id=req.requirement_id,
        event_description=f"Requirement '{req.requirement_code}: {req.requirement_title}' linked to approved source '{source.source_title}' by {actor.full_name}",
        new_values={
            "requirement_code": req.requirement_code,
            "source_id": req.source_id,
            "source_title": source.source_title,
            "section_reference": request.section_reference or serialized_source.section_reference or f"Ref: {req.requirement_code}",
            "source_version": request.source_version or source.version_label,
            "jurisdiction": request.jurisdiction or source.jurisdiction,
            "applicability_notes": request.applicability_notes or source.applicability_rationale,
            "applicability_status": req.applicability_status,
            "requirement_status": req.requirement_status,
        }
    )

    db.commit()
    db.refresh(req)
    return serialize_regulatory_requirement(db, req)


def update_project_requirement(
    db: Session,
    project_id: int,
    requirement_id: int,
    request: RegulatoryRequirementUpdate,
    actor: User
) -> RegulatoryRequirementResponse:
    req = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.requirement_id == requirement_id).first()
    if not req:
        raise NotFoundError(f"Requirement with ID {requirement_id} not found")
    verify_object_belongs_to_project(req.project_id, project_id, "Requirement")

    old_values = {
        "requirement_title": req.requirement_title,
        "applicability_status": req.applicability_status,
        "requirement_status": req.requirement_status
    }

    if request.requirement_title is not None:
        req.requirement_title = request.requirement_title
    if request.requirement_text is not None:
        req.requirement_text = request.requirement_text
    if request.applicability_status is not None:
        req.applicability_status = request.applicability_status
    if request.requirement_status is not None:
        req.requirement_status = request.requirement_status

    req.updated_at = datetime.now(timezone.utc)

    new_vals = {
        "requirement_title": req.requirement_title,
        "applicability_status": req.applicability_status,
        "requirement_status": req.requirement_status
    }
    if request.section_reference is not None:
        new_vals["section_reference"] = request.section_reference
    if request.applicability_notes is not None:
        new_vals["applicability_notes"] = request.applicability_notes

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="REQUIREMENT_UPDATED",
        entity_type="REGULATORY_REQUIREMENT",
        entity_id=req.requirement_id,
        event_description=f"Requirement '{req.requirement_code}' updated by {actor.full_name}",
        old_values=old_values,
        new_values=new_vals
    )

    db.commit()
    db.refresh(req)
    return serialize_regulatory_requirement(db, req)
