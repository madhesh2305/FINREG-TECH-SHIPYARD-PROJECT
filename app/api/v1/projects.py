from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import Project, ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, DashboardSummary
from app.security.authentication import get_current_user
from app.security.authorization import ProjectAccessGuard, require_platform_role, require_project_member, require_project_owner
from app.services.project_service import (
    create_project,
    list_user_projects,
    get_project_by_id,
    update_project,
    get_dashboard_summary,
    calculate_project_progress,
    get_project_workflow_status,
)

router = APIRouter(prefix="/projects", tags=["Project Management"])

@router.get(
    "/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    summary="Get Builder Dashboard Summary",
    description="Returns aggregate counts of active/archived projects, requirements, and members for the current user's authorized projects."
)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_dashboard_summary(db=db, user=current_user)

@router.get(
    "",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="List Authorized Projects",
    description="Lists only projects where the authenticated user has an active project membership. Cross-project data is filtered at database query level."
)
def get_projects(
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(ACTIVE|ARCHIVED)$"),
    search: Optional[str] = Query(None, description="Search term for name or project code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    projects = list_user_projects(db=db, user=current_user, status=status_filter, search=search)
    return [
        ProjectResponse(
            project_id=p.project_id,
            project_name=p.project_name,
            project_code=p.project_code,
            status=p.status,
            created_by=p.created_by,
            owner_name=p.creator.full_name if p.creator else None,
            created_at=p.created_at,
            updated_at=p.updated_at,
            profile=p.profile,
            progress=calculate_project_progress(db=db, project_id=p.project_id)
        )
        for p in projects
    ]

@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Transactionally creates a project, profile, assigns creator as OWNER (PROJECT_CONTROL), and generates an audit event."
)
def create_new_project(
    request: ProjectCreate,
    current_user: User = Depends(require_platform_role("BUILDER", "ADMIN")),
    db: Session = Depends(get_db)
):
    project = create_project(db=db, request=request, creator=current_user)
    return ProjectResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        project_code=project.project_code,
        status=project.status,
        created_by=project.created_by,
        owner_name=current_user.full_name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        profile=project.profile,
        progress=0
    )

from typing import List, Optional, Union

@router.get(
    "/{projectId}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
    description="Returns project details and regulatory profile. Enforces project-level authorization (returns 403 if caller is not an active member)."
)
def get_project(
    projectId: Union[int, str],
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    project = get_project_by_id(db=db, project_id=membership.project_id)
    return ProjectResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        project_code=project.project_code,
        status=project.status,
        created_by=project.created_by,
        owner_name=project.creator.full_name if project.creator else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
        profile=project.profile,
        progress=calculate_project_progress(db=db, project_id=project.project_id)
    )

@router.patch(
    "/{projectId}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Project",
    description="Updates project metadata, status, or regulatory profile. Restricted to project OWNER."
)
def patch_project(
    projectId: Union[int, str],
    request: ProjectUpdate,
    membership: ProjectMember = Depends(require_project_owner),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = update_project(db=db, project_id=membership.project_id, request=request, actor=current_user)
    return ProjectResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        project_code=project.project_code,
        status=project.status,
        created_by=project.created_by,
        owner_name=project.creator.full_name if project.creator else None,
        created_at=project.created_at,
        updated_at=project.updated_at,
        profile=project.profile,
        progress=calculate_project_progress(db=db, project_id=project.project_id)
    )

@router.get(
    "/{projectId}/workflow",
    status_code=status.HTTP_200_OK,
    summary="Get Project Workflow Steps & State",
    description="Returns the 4 structured regulatory workflow steps with live status, completion, and metrics (DEF-30)."
)
def get_project_workflow(
    projectId: Union[int, str],
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    project = get_project_by_id(db=db, project_id=membership.project_id)
    return get_project_workflow_status(db=db, project=project)

@router.get(
    "/{projectId}/workflow/steps/{stepId}",
    status_code=status.HTTP_200_OK,
    summary="Get Project Workflow Step Details",
    description="Returns detailed workflow step status and items (DEF-30)."
)
def get_project_workflow_step(
    projectId: Union[int, str],
    stepId: Union[int, str],
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    project = get_project_by_id(db=db, project_id=membership.project_id)
    workflow_data = get_project_workflow_status(db=db, project=project)
    str_step = str(stepId).strip().lstrip("0")
    for step in workflow_data["steps"]:
        if str(step["step_id"]) == str_step or step["step_number"] == str(stepId).zfill(2) or step["name"].lower() == str(stepId).lower():
            return {
                "project_id": project.project_id,
                "project_code": project.project_code,
                "step": step
            }
    from app.core.exceptions import NotFoundError
    raise NotFoundError(f"Workflow step '{stepId}' not found in project '{project.project_code}'")
