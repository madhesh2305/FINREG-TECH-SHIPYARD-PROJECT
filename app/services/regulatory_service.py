from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, NotFoundError
from app.models.identity import User
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.schemas.regulatory import RegulatorySourceCreate, RegulatoryRequirementCreate, RegulatoryRequirementUpdate
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

def list_regulatory_sources(
    db: Session,
    jurisdiction: Optional[str] = None,
    topic: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[RegulatorySource], int]:
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

    total = query.count()
    items = query.order_by(RegulatorySource.publication_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return items, total

def get_regulatory_source_by_id(db: Session, source_id: int) -> RegulatorySource:
    source = db.query(RegulatorySource).filter(RegulatorySource.source_id == source_id).first()
    if not source:
        raise NotFoundError(f"Regulatory source with ID {source_id} not found")
    return source

def create_regulatory_source(db: Session, request: RegulatorySourceCreate, actor: User) -> RegulatorySource:
    source = RegulatorySource(
        source_title=request.source_title,
        issuing_authority=request.issuing_authority,
        jurisdiction=request.jurisdiction,
        source_url=request.source_url,
        version_label=request.version_label,
        publication_date=request.publication_date,
        retrieved_at=datetime.now(timezone.utc),
        validation_status=request.validation_status,
        topic=request.topic,
        relevance=request.relevance,
        applicability_rationale=request.applicability_rationale,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

def list_project_requirements(
    db: Session,
    project_id: int,
    status: Optional[str] = None,
    applicability: Optional[str] = None
) -> List[RegulatoryRequirement]:
    query = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.project_id == project_id)

    if status:
        query = query.filter(RegulatoryRequirement.requirement_status == status)
    if applicability:
        query = query.filter(RegulatoryRequirement.applicability_status == applicability)

    return query.order_by(RegulatoryRequirement.requirement_code.asc()).all()

def get_project_requirement_by_id(db: Session, project_id: int, requirement_id: int) -> RegulatoryRequirement:
    req = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.requirement_id == requirement_id).first()
    if not req:
        raise NotFoundError(f"Requirement with ID {requirement_id} not found")

    verify_object_belongs_to_project(req.project_id, project_id, "Requirement")
    return req

def create_project_requirement(
    db: Session,
    project_id: int,
    request: RegulatoryRequirementCreate,
    actor: User
) -> RegulatoryRequirement:
    # 1. Provenance validation: Ensure source exists
    source = db.query(RegulatorySource).filter(RegulatorySource.source_id == request.source_id).first()
    if not source:
        raise NotFoundError(f"Approved Regulatory Source with ID {request.source_id} does not exist")

    # 2. Check code uniqueness for project
    existing = db.query(RegulatoryRequirement).filter(
        RegulatoryRequirement.project_id == project_id,
        RegulatoryRequirement.requirement_code == request.requirement_code
    ).first()
    if existing:
        raise ConflictError(f"Requirement with code '{request.requirement_code}' already exists in this project")

    req = RegulatoryRequirement(
        project_id=project_id,
        source_id=request.source_id,
        requirement_code=request.requirement_code,
        requirement_title=request.requirement_title,
        requirement_text=request.requirement_text,
        applicability_status=request.applicability_status,
        requirement_status=request.requirement_status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(req)
    db.flush()

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="REQUIREMENT_CREATED",
        entity_type="REGULATORY_REQUIREMENT",
        entity_id=req.requirement_id,
        event_description=f"Requirement '{req.requirement_code}: {req.requirement_title}' linked to source '{source.source_title}' by {actor.full_name}",
        new_values={
            "requirement_code": req.requirement_code,
            "source_id": req.source_id,
            "source_title": source.source_title,
            "applicability_status": req.applicability_status,
            "requirement_status": req.requirement_status
        }
    )

    db.commit()
    db.refresh(req)
    return req

def update_project_requirement(
    db: Session,
    project_id: int,
    requirement_id: int,
    request: RegulatoryRequirementUpdate,
    actor: User
) -> RegulatoryRequirement:
    req = get_project_requirement_by_id(db, project_id, requirement_id)

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

    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="REQUIREMENT_UPDATED",
        entity_type="REGULATORY_REQUIREMENT",
        entity_id=req.requirement_id,
        event_description=f"Requirement '{req.requirement_code}' updated by {actor.full_name}",
        old_values=old_values,
        new_values={
            "requirement_title": req.requirement_title,
            "applicability_status": req.applicability_status,
            "requirement_status": req.requirement_status
        }
    )

    db.commit()
    db.refresh(req)
    return req
