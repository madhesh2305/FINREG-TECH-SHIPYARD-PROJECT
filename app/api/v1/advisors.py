from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.models.advisor import AdvisorProfile, AdvisorInvitation
from app.schemas.advisor import (
    AdvisorProfileResponse,
    AdvisorInvitationCreate,
    AdvisorInvitationResponse
)
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member, require_project_owner
from app.services.advisor_service import (
    list_advisors,
    get_advisor_by_id,
    create_advisor_invitation,
    list_advisor_invitations,
    resend_advisor_invitation,
    revoke_advisor_invitation
)

router = APIRouter(tags=["Advisors & Invitations"])

def _to_advisor_response(a: AdvisorProfile) -> AdvisorProfileResponse:
    return AdvisorProfileResponse(
        advisor_profile_id=a.advisor_profile_id,
        user_id=a.user_id,
        full_name=a.user.full_name if a.user else "Unknown",
        email=a.user.email if a.user else "",
        organization_name=a.organization_name,
        professional_title=a.professional_title,
        specialization=a.specialization,
        bio=a.bio or "",
        created_at=a.created_at,
        updated_at=a.updated_at
    )

# -------------------------------------------------------------
# Global Advisor Directory
# -------------------------------------------------------------

@router.get(
    "/advisors",
    response_model=List[AdvisorProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List Verified Advisors",
    description="Returns public profiles of all registered and verified FCC advisors available across the platform."
)
def get_advisors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    advisors = list_advisors(db=db)
    return [_to_advisor_response(a) for a in advisors]

@router.get(
    "/advisors/{advisorId}",
    response_model=AdvisorProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Advisor Profile",
    description="Returns detailed profile of a specific advisor by advisor_profile_id."
)
def get_advisor(
    advisorId: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    advisor = get_advisor_by_id(db=db, advisor_id=advisorId)
    return _to_advisor_response(advisor)

# -------------------------------------------------------------
# Project Advisor Invitations (Scoped under /projects/{projectId})
# -------------------------------------------------------------

@router.get(
    "/projects/{projectId}/advisor-invitations",
    response_model=List[AdvisorInvitationResponse],
    status_code=status.HTTP_200_OK,
    summary="List Project Advisor Invitations",
    description="Lists all advisor invitations issued for this project. Caller must be an active project member."
)
def get_project_invitations(
    projectId: int,
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db)
):
    return list_advisor_invitations(db=db, project_id=projectId)

@router.post(
    "/projects/{projectId}/advisor-invitations",
    response_model=AdvisorInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite Advisor to Project",
    description="Issues an advisor invitation token with expiration. Requires project OWNER role."
)
def invite_advisor(
    projectId: int,
    request: AdvisorInvitationCreate,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_owner),
    db: Session = Depends(get_db)
):
    return create_advisor_invitation(db=db, project_id=projectId, request=request, actor=current_user)

@router.post(
    "/projects/{projectId}/advisor-invitations/{invitationId}/resend",
    response_model=AdvisorInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend Advisor Invitation",
    description="Regenerates invitation token and extends expiration. Requires project OWNER role. Validates project boundaries."
)
def resend_invitation(
    projectId: int,
    invitationId: int,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_owner),
    db: Session = Depends(get_db)
):
    return resend_advisor_invitation(db=db, project_id=projectId, invitation_id=invitationId, actor=current_user)

@router.post(
    "/projects/{projectId}/advisor-invitations/{invitationId}/revoke",
    response_model=AdvisorInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke Advisor Invitation",
    description="Marks a pending invitation as REVOKED. Requires project OWNER role. Validates project boundaries."
)
def revoke_invitation(
    projectId: int,
    invitationId: int,
    current_user: User = Depends(get_current_user),
    membership: ProjectMember = Depends(require_project_owner),
    db: Session = Depends(get_db)
):
    return revoke_advisor_invitation(db=db, project_id=projectId, invitation_id=invitationId, actor=current_user)
