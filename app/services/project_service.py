from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.exceptions import ConflictError, NotFoundError
from app.models.identity import User
from app.models.project import Project, ProjectProfile, ProjectMember
from app.models.regulatory import RegulatoryRequirement
from app.schemas.project import ProjectCreate, ProjectUpdate, DashboardSummary
from app.services.audit_service import log_audit_event

def create_project(db: Session, request: ProjectCreate, creator: User) -> Project:
    """Transactionally create project, profile, owner membership and audit event."""
    existing = db.query(Project).filter(Project.project_code == request.project_code).first()
    if existing:
        raise ConflictError(f"Project with code '{request.project_code}' already exists")

    # 1. Create project
    project = Project(
        project_name=request.project_name,
        project_code=request.project_code,
        status="ACTIVE",
        created_by=creator.user_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(project)
    db.flush()

    # 2. Create project profile
    profile = ProjectProfile(
        project_id=project.project_id,
        description=request.description,
        jurisdiction=request.jurisdiction,
        regulatory_scope=request.regulatory_scope,
        objectives=request.objectives,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(profile)
    db.flush()

    # 3. Create initial OWNER membership for creator
    owner_member = ProjectMember(
        project_id=project.project_id,
        user_id=creator.user_id,
        service_role="OWNER",
        service_scope="PROJECT_CONTROL",
        member_status="ACTIVE",
        joined_at=datetime.now(timezone.utc)
    )
    db.add(owner_member)
    db.flush()

    # 4. Generate audit event
    log_audit_event(
        db=db,
        project_id=project.project_id,
        actor_user_id=creator.user_id,
        event_type="PROJECT_CREATED",
        entity_type="PROJECT",
        entity_id=project.project_id,
        event_description=f"Project '{project.project_name}' ({project.project_code}) created by {creator.full_name}",
        new_values={
            "project_name": project.project_name,
            "project_code": project.project_code,
            "status": project.status,
            "jurisdiction": profile.jurisdiction,
            "regulatory_scope": profile.regulatory_scope
        }
    )

    db.commit()
    db.refresh(project)
    return project

def list_user_projects(db: Session, user: User, status: Optional[str] = None, search: Optional[str] = None) -> List[Project]:
    """Return projects accessible to the user via active project membership."""
    query = (
        db.query(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.project_id)
        .filter(
            ProjectMember.user_id == user.user_id,
            ProjectMember.member_status == "ACTIVE"
        )
    )

    if status:
        query = query.filter(Project.status == status)

    if search:
        pattern = f"%{search}%"
        query = query.filter((Project.project_name.ilike(pattern)) | (Project.project_code.ilike(pattern)))

    return query.order_by(Project.updated_at.desc()).all()

def get_project_by_id(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise NotFoundError(f"Project with ID {project_id} not found")
    return project

def update_project(db: Session, project_id: int, request: ProjectUpdate, actor: User) -> Project:
    project = get_project_by_id(db, project_id)
    old_values = {
        "project_name": project.project_name,
        "status": project.status
    }
    
    if request.project_name is not None:
        project.project_name = request.project_name
    if request.status is not None:
        project.status = request.status
        
    project.updated_at = datetime.now(timezone.utc)

    if project.profile:
        old_values.update({
            "description": project.profile.description,
            "jurisdiction": project.profile.jurisdiction,
            "regulatory_scope": project.profile.regulatory_scope,
            "objectives": project.profile.objectives
        })
        if request.description is not None:
            project.profile.description = request.description
        if request.jurisdiction is not None:
            project.profile.jurisdiction = request.jurisdiction
        if request.regulatory_scope is not None:
            project.profile.regulatory_scope = request.regulatory_scope
        if request.objectives is not None:
            project.profile.objectives = request.objectives
        project.profile.updated_at = datetime.now(timezone.utc)

    new_values = {
        "project_name": project.project_name,
        "status": project.status
    }
    if project.profile:
        new_values.update({
            "description": project.profile.description,
            "jurisdiction": project.profile.jurisdiction,
            "regulatory_scope": project.profile.regulatory_scope,
            "objectives": project.profile.objectives
        })

    log_audit_event(
        db=db,
        project_id=project.project_id,
        actor_user_id=actor.user_id,
        event_type="PROJECT_UPDATED",
        entity_type="PROJECT",
        entity_id=project.project_id,
        event_description=f"Project '{project.project_name}' updated by {actor.full_name}",
        old_values=old_values,
        new_values=new_values
    )

    db.commit()
    db.refresh(project)
    return project

def get_dashboard_summary(db: Session, user: User) -> DashboardSummary:
    """Calculate dashboard metrics based only on real authoritative project data."""
    user_project_ids = [
        r[0] for r in db.query(ProjectMember.project_id)
        .filter(ProjectMember.user_id == user.user_id, ProjectMember.member_status == "ACTIVE")
        .all()
    ]

    if not user_project_ids:
        return DashboardSummary(
            total_projects=0,
            active_projects=0,
            archived_projects=0,
            total_requirements=0,
            total_members=0,
            open_requirements=0,
            completed_requirements=0
        )

    total_projects = db.query(Project).filter(Project.project_id.in_(user_project_ids)).count()
    active_projects = db.query(Project).filter(Project.project_id.in_(user_project_ids), Project.status == "ACTIVE").count()
    archived_projects = db.query(Project).filter(Project.project_id.in_(user_project_ids), Project.status == "ARCHIVED").count()

    total_reqs = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.project_id.in_(user_project_ids)).count()
    open_reqs = db.query(RegulatoryRequirement).filter(
        RegulatoryRequirement.project_id.in_(user_project_ids),
        RegulatoryRequirement.requirement_status == "OPEN"
    ).count()
    completed_reqs = db.query(RegulatoryRequirement).filter(
        RegulatoryRequirement.project_id.in_(user_project_ids),
        RegulatoryRequirement.requirement_status == "COMPLETED"
    ).count()

    total_members = db.query(ProjectMember).filter(
        ProjectMember.project_id.in_(user_project_ids),
        ProjectMember.member_status == "ACTIVE"
    ).count()

    return DashboardSummary(
        total_projects=total_projects,
        active_projects=active_projects,
        archived_projects=archived_projects,
        total_requirements=total_reqs,
        total_members=total_members,
        open_requirements=open_reqs,
        completed_requirements=completed_reqs
    )
