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

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=4, description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to request password reset for")

class PasswordResetResponse(BaseModel):
    status: str
    message: str
    delivery_channel: str
    reset_token: str | None = Field(None, description="Password reset token issued for test/local workflow")

class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(..., description="Password reset token received from reset request")
    new_password: str = Field(..., min_length=6, description="New account password (min 6 characters)")
