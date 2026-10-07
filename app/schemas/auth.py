from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=4, description="User password")

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=4, description="User password")
    full_name: str = Field(..., min_length=2, description="User full name")
    role: str = Field("BUILDER", description="Platform role: BUILDER, ADVISOR, or ADMIN")
    organization: str | None = Field(None, description="Organization name (for advisors or builders)")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    full_name: str
    email: str
    platform_role: str
