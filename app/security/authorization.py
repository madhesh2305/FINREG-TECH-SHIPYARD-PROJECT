from typing import Callable, List, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.session import get_db
from app.models.identity import User
from app.models.project import Project, ProjectMember
from app.security.authentication import get_current_user

def require_platform_role(*allowed_roles: str) -> Callable:
    """Dependency that enforces platform-level role (ADMIN, BUILDER, ADVISOR)."""
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not user.role or user.role.role_name not in allowed_roles:
            raise ForbiddenError(f"Action requires one of the following platform roles: {', '.join(allowed_roles)}")
        return user
    return dependency

class ProjectAccessGuard:
    """
    Project-level authorization guard.
    Sequence:
    1. Authenticate user
    2. Check project existence
    3. Enforce active project membership (No automatic platform ADMIN bypass)
    4. Optional check on service_role (e.g. OWNER, LEGAL, REGULATORY)
    """
    def __init__(self, required_service_roles: Optional[List[str]] = None):
        self.required_service_roles = required_service_roles

    def __call__(
        self,
        projectId: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ) -> ProjectMember:
        # Step 1: Project existence check
        project = db.query(Project).filter(Project.project_id == projectId).first()
        if not project:
            raise NotFoundError(f"Project with ID {projectId} not found")

        # Step 2: Strict project membership check (Platform ADMIN does NOT bypass project isolation)
        membership = db.query(ProjectMember).filter(
            ProjectMember.project_id == projectId,
            ProjectMember.user_id == current_user.user_id,
            ProjectMember.member_status == "ACTIVE"
        ).first()

        if not membership:
            raise ForbiddenError("You are not an active member of this project")

        # Step 3: Service role check if specified
        if self.required_service_roles and membership.service_role not in self.required_service_roles:
            roles_str = ", ".join(self.required_service_roles)
            raise ForbiddenError(f"Action requires project service role: {roles_str} (your role: {membership.service_role})")

        return membership

def require_project_member(projectId: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectMember:
    guard = ProjectAccessGuard()
    return guard(projectId=projectId, db=db, current_user=user)

def require_project_owner(projectId: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectMember:
    guard = ProjectAccessGuard(required_service_roles=["OWNER"])
    return guard(projectId=projectId, db=db, current_user=user)

def verify_object_belongs_to_project(object_project_id: int, expected_project_id: int, resource_name: str = "Resource"):
    """BOLA / IDOR defense: Ensure requested object strictly belongs to the path project."""
    if object_project_id != expected_project_id:
        raise NotFoundError(f"{resource_name} not found in this project")
