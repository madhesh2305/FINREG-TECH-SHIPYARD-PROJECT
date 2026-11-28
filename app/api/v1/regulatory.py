import math
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.identity import User
from app.models.project import Project, ProjectMember
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.schemas.common import PaginatedResponse
from app.schemas.regulatory import (
    RegulatorySourceCreate,
    RegulatorySourceResponse,
    RegulatorySourceValidationRequest,
    RegulatoryRequirementCreate,
    RegulatoryRequirementUpdate,
    RegulatoryRequirementResponse,
)
from app.security.authentication import get_current_user
from app.security.authorization import ProjectAccessGuard, require_platform_role, require_project_member
from app.services.regulatory_service import (
    create_project_requirement,
    create_regulatory_source,
    get_project_requirement_by_id,
    get_regulatory_source_by_id,
    jurisdictions_match,
    list_advisor_assigned_requirements,
    list_project_requirements,
    list_regulatory_sources,
    serialize_regulatory_source,
    serialize_regulatory_sources,
    update_project_requirement,
    validate_regulatory_source,
)

router = APIRouter(tags=["Regulatory Intelligence"])

# -------------------------------------------------------------
# Global Regulatory Sources Corpus
# -------------------------------------------------------------

@router.get(
    "/regulatory/sources",
    response_model=PaginatedResponse[RegulatorySourceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Regulatory Sources",
    description="Returns persisted regulatory sources with official URL/document, provenance, validation state, and reviewer metadata."
)
def get_sources(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction, e.g. UK, EU"),
    topic: Optional[str] = Query(None, description="Filter by topic, e.g. AML, CDD, Reporting"),
    search: Optional[str] = Query(None, description="Free text search in title, authority, relevance"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by validation status or state"),
    validation_state: Optional[str] = Query(None, description="Filter by validation state (PENDING_VALIDATION, APPROVED, REJECTED, CHANGES_REQUESTED)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = list_regulatory_sources(
        db=db,
        jurisdiction=jurisdiction,
        topic=topic,
        search=search,
        validation_state=validation_state or status_filter,
        page=page,
        page_size=page_size,
    )
    pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse[RegulatorySourceResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )

@router.get(
    "/regulatory/sources/{sourceId}",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Regulatory Source Details",
    description="Returns detailed metadata, provenance, validation state, and official publication reference for a regulatory source."
)
def get_source(
    sourceId: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_regulatory_source_by_id(db=db, source_id=sourceId)

@router.post(
    "/regulatory/sources",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Regulatory Source for Validation",
    description="Submits a regulatory source with official URL or document and provenance metadata in PENDING validation state. Restricted to ADMIN and BUILDER."
)
def create_source(
    request: RegulatorySourceCreate,
    current_user: User = Depends(require_platform_role("ADMIN", "BUILDER")),
    db: Session = Depends(get_db)
):
    return create_regulatory_source(db=db, request=request, actor=current_user)

@router.patch(
    "/regulatory/sources/{sourceId}/validate",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate, Reject, or Request Changes on Regulatory Source",
    description="Records reviewer, timestamp, decision (APPROVED, REJECTED, CHANGES_REQUESTED), and rationale. Restricted to ADMIN."
)
def validate_source_endpoint(
    sourceId: int,
    request: RegulatorySourceValidationRequest,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return validate_regulatory_source(db=db, source_id=sourceId, request=request, reviewer=current_user)

@router.post(
    "/regulatory/sources/{sourceId}/approve",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Regulatory Source",
    description="Approves a regulatory source for downstream requirement extraction. Restricted to ADMIN."
)
def approve_source_endpoint(
    sourceId: int,
    reason: Optional[str] = Query(None, max_length=1000),
    body: Optional[RegulatorySourceValidationRequest] = None,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    req_reason = (body.reason if body else None) or reason
    return validate_regulatory_source(
        db=db,
        source_id=sourceId,
        request=RegulatorySourceValidationRequest(decision="APPROVED", reason=req_reason),
        reviewer=current_user,
    )

@router.post(
    "/regulatory/sources/{sourceId}/reject",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Regulatory Source",
    description="Rejects a regulatory source with mandatory reviewer rationale. Restricted to ADMIN."
)
def reject_source_endpoint(
    sourceId: int,
    request: RegulatorySourceValidationRequest,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return validate_regulatory_source(
        db=db,
        source_id=sourceId,
        request=RegulatorySourceValidationRequest(decision="REJECTED", reason=request.reason),
        reviewer=current_user,
    )

@router.post(
    "/regulatory/sources/{sourceId}/request-changes",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Changes on Regulatory Source",
    description="Marks a regulatory source as CHANGES_REQUESTED with mandatory reviewer rationale. Restricted to ADMIN."
)
def request_changes_source_endpoint(
    sourceId: int,
    request: RegulatorySourceValidationRequest,
    current_user: User = Depends(require_platform_role("ADMIN")),
    db: Session = Depends(get_db)
):
    return validate_regulatory_source(
        db=db,
        source_id=sourceId,
        request=RegulatorySourceValidationRequest(decision="CHANGES_REQUESTED", reason=request.reason),
        reviewer=current_user,
    )

# -------------------------------------------------------------
# Global Regulatory Requirements Library (Consumed by frontend Regulatory Support view)
# -------------------------------------------------------------

@router.get(
    "/regulatory-requirements",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="List Regulatory Corpus Requirements",
    description="Returns curated regulatory library records derived from approved sources, optionally scoped by project, jurisdiction, or topic."
)
def get_global_regulatory_requirements(
    approved_only: bool = Query(True, description="When true, excludes pending/rejected/changes-requested sources"),
    project_id: Optional[Union[int, str]] = Query(None, description="Optional project ID/code to scope to project jurisdiction & scope"),
    jurisdiction: Optional[str] = Query(None, description="Optional jurisdiction filter"),
    scope: Optional[str] = Query(None, description="Optional topic/scope filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_jurisdiction = jurisdiction
    target_scope = scope
    if project_id is not None:
        guard = ProjectAccessGuard()
        membership = guard(projectId=project_id, current_user=current_user, db=db)
        project = db.query(Project).filter(Project.project_id == membership.project_id).first()
        if project and project.profile:
            if not target_jurisdiction:
                target_jurisdiction = project.profile.jurisdiction
            if not target_scope:
                target_scope = project.profile.regulatory_scope

    raw_sources = db.query(RegulatorySource).order_by(RegulatorySource.source_id.asc()).all()
    sources = serialize_regulatory_sources(db, raw_sources)
    results = []
    for s in sources:
        is_approved = (s.validation_status == "VALIDATED" and s.validation_state == "APPROVED")
        if approved_only and not is_approved:
            continue
        if target_jurisdiction and not jurisdictions_match(target_jurisdiction, s.jurisdiction):
            continue
        if target_scope:
            scope_l = target_scope.lower()
            text_blob = f"{s.topic} {s.source_title} {s.relevance}".lower()
            if not any(tok in text_blob for tok in scope_l.replace("&", " ").replace("(", " ").replace(")", " ").split() if len(tok) >= 3):
                continue

        results.append({
            "id": f"REQ-{s.source_id:03d}",
            "source_id": s.source_id,
            "code": s.source_code or f"SRC-{s.source_id:03d}",
            "title": s.source_title,
            "requirement": s.source_title,
            "authority": s.issuing_authority,
            "jurisdiction": s.jurisdiction,
            "source": s.source_title,
            "provenance": s.provenance or s.version_label,
            "reference": s.section_reference or s.version_label or f"SRC-{s.source_id:03d}",
            "sectionReference": s.section_reference or s.version_label,
            "version": s.version_label,
            "dateVersion": str(s.publication_date) if s.publication_date else s.version_label,
            "layer": s.topic,
            "category": s.topic,
            "topic": s.topic,
            "applicability": s.applicability_notes or s.applicability_rationale or "Requires per-project applicability verification",
            "validationState": s.validation_state,
            "validationStatus": "Validated" if is_approved else s.validation_state,
            "status": "Validated" if is_approved else s.validation_state,
            "reviewerName": s.reviewer_name,
            "reviewedAt": s.reviewed_at.isoformat() if s.reviewed_at else None,
            "reviewReason": s.review_reason,
            "documentName": s.document_name,
            "sourceUrl": s.source_url,
            "description": s.relevance or s.source_title,
        })
    return results

@router.get(
    "/regulatory-requirements/{reqId}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get Regulatory Corpus Requirement Details"
)
def get_global_regulatory_requirement_details(
    reqId: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clean_id = reqId.replace("REQ-", "").replace("SRC-", "")
    source = None
    if clean_id.isdigit():
        source = db.query(RegulatorySource).filter(RegulatorySource.source_id == int(clean_id)).first()
    if not source:
        source = db.query(RegulatorySource).filter(RegulatorySource.source_title.ilike(f"%{clean_id}%")).first()
    if not source:
        req = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.requirement_code == reqId).first()
        if req:
            # Verify caller belongs to that requirement's project to prevent IDOR
            guard = ProjectAccessGuard()
            guard(projectId=req.project_id, current_user=current_user, db=db)
            return {
                "id": req.requirement_code,
                "code": req.requirement_code,
                "title": req.requirement_title,
                "description": req.requirement_text,
                "status": req.requirement_status,
                "applicability": req.applicability_status,
            }
        raise NotFoundError(f"Regulatory requirement '{reqId}' not found")
    s = serialize_regulatory_source(db, source)
    is_approved = (s.validation_status == "VALIDATED" and s.validation_state == "APPROVED")
    return {
        "id": f"REQ-{s.source_id:03d}",
        "code": s.source_code or f"SRC-{s.source_id:03d}",
        "source_id": s.source_id,
        "title": s.source_title,
        "authority": s.issuing_authority,
        "jurisdiction": s.jurisdiction,
        "provenance": s.provenance,
        "version": s.version_label,
        "sectionReference": s.section_reference or s.version_label,
        "documentName": s.document_name,
        "sourceUrl": s.source_url,
        "validationState": s.validation_state,
        "status": "Validated" if is_approved else s.validation_state,
        "reviewerName": s.reviewer_name,
        "reviewedAt": s.reviewed_at.isoformat() if s.reviewed_at else None,
        "reviewReason": s.review_reason,
        "description": s.relevance,
    }

# -------------------------------------------------------------
# Advisor Assigned Project Requirements (Scoped to Accepted Assignments ONLY)
# -------------------------------------------------------------

@router.get(
    "/advisors/me/requirements",
    response_model=List[RegulatoryRequirementResponse],
    status_code=status.HTTP_200_OK,
    summary="List Requirements for Advisor's Accepted Projects",
    description="Returns ONLY regulatory requirements belonging to projects where the authenticated advisor has accepted/active assignment."
)
def get_my_advisor_requirements(
    project_id: Optional[Union[int, str]] = Query(None, description="Optional project ID or code (requires accepted membership)"),
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$"),
    applicability_filter: Optional[str] = Query(None, alias="applicability", pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$"),
    jurisdiction: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resolved_pid = None
    if project_id is not None:
        if isinstance(project_id, int) or (isinstance(project_id, str) and str(project_id).isdigit()):
            resolved_pid = int(project_id)
        else:
            p = db.query(Project).filter(Project.project_code == str(project_id)).first()
            if not p:
                raise NotFoundError(f"Project '{project_id}' not found")
            resolved_pid = p.project_id

    return list_advisor_assigned_requirements(
        db=db,
        user=current_user,
        project_id=resolved_pid,
        status=status_filter,
        applicability=applicability_filter,
        jurisdiction=jurisdiction,
    )

# -------------------------------------------------------------
# Project Regulatory Requirements (Scoped under /projects/{projectId})
# -------------------------------------------------------------

@router.get(
    "/projects/{projectId}/requirements",
    response_model=List[RegulatoryRequirementResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Requirements",
    description="Returns regulatory compliance requirements linked to this project, optionally scoped by project jurisdiction and scope. Requires active project membership."
)
def get_requirements(
    projectId: Union[int, str],
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$"),
    applicability_filter: Optional[str] = Query(None, alias="applicability", pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    scope: Optional[str] = Query(None, description="Filter by regulatory scope/topic"),
    scoped_only: bool = Query(False, description="When true, restricts results to the project's profile jurisdiction"),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    effective_jurisdiction = jurisdiction
    if scoped_only and not effective_jurisdiction:
        project = db.query(Project).filter(Project.project_id == membership.project_id).first()
        if project and project.profile:
            effective_jurisdiction = project.profile.jurisdiction

    return list_project_requirements(
        db=db,
        project_id=membership.project_id,
        status=status_filter,
        applicability=applicability_filter,
        jurisdiction=effective_jurisdiction,
        scope=scope,
    )

@router.post(
    "/projects/{projectId}/requirements",
    response_model=RegulatoryRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project Requirement",
    description="Maps a project requirement to an approved regulatory source. Validates source provenance and logs audit event."
)
def create_requirement(
    projectId: Union[int, str],
    request: RegulatoryRequirementCreate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return create_project_requirement(
        db=db,
        project_id=membership.project_id,
        request=request,
        actor=current_user
    )

@router.get(
    "/projects/{projectId}/requirements/{requirementId}",
    response_model=RegulatoryRequirementResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Requirement Details",
    description="Returns requirement details with associated source metadata. Validates cross-project isolation."
)
def get_requirement(
    projectId: Union[int, str],
    requirementId: int,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return get_project_requirement_by_id(db=db, project_id=membership.project_id, requirement_id=requirementId)

@router.patch(
    "/projects/{projectId}/requirements/{requirementId}",
    response_model=RegulatoryRequirementResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Project Requirement",
    description="Updates requirement title, text, applicability or workflow status. Validates project boundaries and logs audit event."
)
def update_requirement(
    projectId: Union[int, str],
    requirementId: int,
    request: RegulatoryRequirementUpdate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return update_project_requirement(
        db=db,
        project_id=membership.project_id,
        requirement_id=requirementId,
        request=request,
        actor=current_user
    )
