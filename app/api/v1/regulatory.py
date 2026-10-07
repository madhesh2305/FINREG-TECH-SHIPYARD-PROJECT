import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.schemas.common import PaginatedResponse
from app.schemas.regulatory import (
    RegulatorySourceCreate,
    RegulatorySourceResponse,
    RegulatoryRequirementCreate,
    RegulatoryRequirementUpdate,
    RegulatoryRequirementResponse
)
from app.security.authentication import get_current_user
from app.security.authorization import require_platform_role, require_project_member
from app.services.regulatory_service import (
    list_regulatory_sources,
    get_regulatory_source_by_id,
    create_regulatory_source,
    list_project_requirements,
    get_project_requirement_by_id,
    create_project_requirement,
    update_project_requirement
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
    description="Returns verified, copyright-safe regulatory sources with provenance metadata, issuing authority, and compliance applicability."
)
def get_sources(
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction, e.g. UK, EU"),
    topic: Optional[str] = Query(None, description="Filter by topic, e.g. AML, CDD, Reporting"),
    search: Optional[str] = Query(None, description="Free text search in title, authority, relevance"),
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
        page=page,
        page_size=page_size
    )
    pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse[RegulatorySourceResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )

@router.get(
    "/regulatory/sources/{sourceId}",
    response_model=RegulatorySourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Regulatory Source Details",
    description="Returns detailed metadata and official publication reference for a specific regulatory source."
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
    summary="Register Regulatory Source",
    description="Adds a newly validated regulatory source to the platform corpus. Restricted to ADMIN and BUILDER."
)
def create_source(
    request: RegulatorySourceCreate,
    current_user: User = Depends(require_platform_role("ADMIN", "BUILDER")),
    db: Session = Depends(get_db)
):
    return create_regulatory_source(db=db, request=request, actor=current_user)

# -------------------------------------------------------------
# Project Regulatory Requirements (Scoped under /projects/{projectId})
# -------------------------------------------------------------

@router.get(
    "/projects/{projectId}/requirements",
    response_model=List[RegulatoryRequirementResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Requirements",
    description="Returns all regulatory compliance requirements linked to this project. Requires project membership."
)
def get_requirements(
    projectId: int,
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(OPEN|IN_REVIEW|COMPLETED|BLOCKED)$"),
    applicability_filter: Optional[str] = Query(None, alias="applicability", pattern="^(APPLICABLE|NOT_APPLICABLE|UNDER_REVIEW)$"),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return list_project_requirements(
        db=db,
        project_id=projectId,
        status=status_filter,
        applicability=applicability_filter
    )

@router.post(
    "/projects/{projectId}/requirements",
    response_model=RegulatoryRequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project Requirement",
    description="Maps a project requirement to an approved regulatory source. Validates source provenance and logs audit event."
)
def create_requirement(
    projectId: int,
    request: RegulatoryRequirementCreate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return create_project_requirement(
        db=db,
        project_id=projectId,
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
    projectId: int,
    requirementId: int,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return get_project_requirement_by_id(db=db, project_id=projectId, requirement_id=requirementId)

@router.patch(
    "/projects/{projectId}/requirements/{requirementId}",
    response_model=RegulatoryRequirementResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Project Requirement",
    description="Updates requirement title, text, applicability or workflow status. Validates project boundaries and logs audit event."
)
def update_requirement(
    projectId: int,
    requirementId: int,
    request: RegulatoryRequirementUpdate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return update_project_requirement(
        db=db,
        project_id=projectId,
        requirement_id=requirementId,
        request=request,
        actor=current_user
    )
