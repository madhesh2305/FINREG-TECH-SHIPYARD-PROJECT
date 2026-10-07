from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class UserMembershipContext(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    service_role: str
    service_scope: str
    member_status: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr
    is_active: bool
    platform_role: str
    created_at: datetime
    updated_at: datetime

class CurrentUserContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    full_name: str
    email: EmailStr
    is_active: bool
    platform_role: str
    memberships: List[UserMembershipContext] = []
