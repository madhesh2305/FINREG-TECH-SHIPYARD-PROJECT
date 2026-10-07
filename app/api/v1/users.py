from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.user import CurrentUserContext, UserMembershipContext
from app.security.authentication import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/me",
    response_model=CurrentUserContext,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile & Context",
    description="Returns the authenticated user's profile, platform role, and active project memberships with service roles and scopes."
)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Load user's active project memberships
    memberships = (
        db.query(ProjectMember)
        .filter(ProjectMember.user_id == current_user.user_id, ProjectMember.member_status == "ACTIVE")
        .all()
    )

    membership_contexts = [
        UserMembershipContext(
            project_id=m.project_id,
            project_name=m.project.project_name if m.project else "Unknown",
            project_code=m.project.project_code if m.project else "",
            service_role=m.service_role,
            service_scope=m.service_scope,
            member_status=m.member_status
        )
        for m in memberships
    ]

    return CurrentUserContext(
        user_id=current_user.user_id,
        full_name=current_user.full_name,
        email=current_user.email,
        is_active=current_user.is_active,
        platform_role=current_user.role.role_name if current_user.role else "USER",
        memberships=membership_contexts
    )
