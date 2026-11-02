from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class AdvisorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    advisor_profile_id: int
    user_id: int
    full_name: str
    email: EmailStr
    organization_name: str
    professional_title: str
    specialization: str
    bio: str
    created_at: datetime
    updated_at: datetime

class AdvisorInvitationCreate(BaseModel):
    advisor_email: EmailStr = Field(..., description="Email address of advisor")
    access_level: str = Field(..., description="Service role to assign: LEGAL, REGULATORY, TECH, FUNDING_BUSINESS, MARKETING")
    expiry_days: int = Field(7, ge=1, le=30, description="Validity period in days")

class AdvisorInvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invitation_id: int
    project_id: int
    invited_by: int
    advisor_email: EmailStr
    access_level: str
    invitation_status: str
    invitation_token: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime

class AdvisorSelectionRequest(BaseModel):
    advisor_id: Optional[int] = Field(None, description="User ID or Advisor Profile ID of the selected advisor")
    advisor_email: Optional[EmailStr] = Field(None, description="Email address of the selected advisor")
    access_level: str = Field("REGULATORY", description="Role: REGULATORY, LEGAL, TECH, FUNDING_BUSINESS, MARKETING")
    expiry_days: int = Field(7, ge=1, le=30)

class AdvisorInboxInvitation(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invitation_id: int
    project_id: int
    project_code: str
    project_name: str
    inviting_user: str
    access_level: str
    status: str
    invitation_token: str
    expires_at: datetime
    created_at: datetime
