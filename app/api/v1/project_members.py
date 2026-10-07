from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member, require_project_owner
from app.services.member_service import (
    list_project_members,
    add_project_member,
    update_project_member,
    revoke_project_member
)

router = APIRouter(prefix="/projects/{projectId}/members", tags=["Project Members"])

def _to_member_response(m: ProjectMember) -> MemberResponse:
    return MemberResponse(
        project_member_id=m.project_member_id,
        project_id=m.project_id,
        user_id=m.user_id,
        full_name=m.user.full_name if m.user else "Unknown",
        email=m.user.email if m.user else "",
        platform_role=m.user.role.role_name if (m.user and m.user.role) else "BUILDER",
        service_role=m.service_role,
        service_scope=m.service_scope,
        member_status=m.member_status,
        joined_at=m.joined_at
    )

@router.get(
    "",
    response_model=List[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Members",
    description="Returns all active members assigned to the project. Caller must be an active member of this project."
)
def get_members(
    projectId: int,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    members = list_project_members(db=db, project_id=projectId)
    return [_to_member_response(m) for m in members]

@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Project Member",
    description="Adds an existing platform user to this project with a project service role. Requires project OWNER role."
)
def add_member(
    projectId: int,
    request: MemberCreate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_owner),
    db: Session = Depends(get_db)
):
    member = add_project_member(db=db, project_id=projectId, request=request, actor=current_user)
    return _to_member_response(member)

@router.patch(
    "/{memberId}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Project Member",
    description="Updates a member's service role, scope, or status. Requires project OWNER role. Validates project boundaries."
)
def update_member(
    projectId: int,
    memberId: int,
    request: MemberUpdate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_owner),
    db: Session = Depends(get_db)
):
    member = update_project_member(db=db, project_id=projectId, member_id=memberId, request=request, actor=current_user)
    return _to_member_response(member)

@router.delete(
    "/{memberId}",
    response_model=MemberResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke Project Member",
    description="Revokes a project member's access (soft delete / status='REVOKED'). Requires project OWNER role."
)
def revoke_member(
    projectId: int,
    memberId: int,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_owner),
    db: Session = Depends(get_db)
):
    member = revoke_project_member(db=db, project_id=projectId, member_id=memberId, actor=current_user)
    return _to_member_response(member)
