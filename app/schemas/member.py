from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

VALID_SERVICE_ROLES = ("OWNER", "LEGAL", "REGULATORY", "TECH", "FUNDING_BUSINESS", "MARKETING")
VALID_MEMBER_STATUSES = ("ACTIVE", "REVOKED")

ROLE_TO_DEFAULT_SCOPE = {
    "OWNER": "PROJECT_CONTROL",
    "LEGAL": "LEGAL_ADVICE_SUPPORT",
    "REGULATORY": "REGULATORY_ADVICE_SUPPORT",
    "TECH": "TECH_SOLUTION_SUPPORT",
    "FUNDING_BUSINESS": "FUNDING_BUSINESS_SUPPORT",
    "MARKETING": "MARKETING_SUPPORT"
}

class MemberCreate(BaseModel):
    user_id: int = Field(..., description="ID of the platform user to add to project")
    service_role: str = Field(..., description="Project service role: OWNER, LEGAL, REGULATORY, TECH, FUNDING_BUSINESS, MARKETING")
    service_scope: Optional[str] = Field(None, description="Optional custom scope; defaults to canonical role scope")

class MemberUpdate(BaseModel):
    service_role: Optional[str] = Field(None, description="New service role")
    service_scope: Optional[str] = Field(None, description="New service scope")
    member_status: Optional[str] = Field(None, pattern="^(ACTIVE|REVOKED)$", description="Membership status")

class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_member_id: int
    project_id: int
    user_id: int
    full_name: str
    email: str
    platform_role: str
    service_role: str
    service_scope: str
    member_status: str
    joined_at: datetime
