from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.core.security import revoke_token
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
    change_user_password,
    request_password_reset,
    confirm_password_reset,
)
from app.security.authentication import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke Current User Session & Token",
    description="Securely revokes caller's JWT bearer token in PostgreSQL and memory, preventing reuse across all subsequent requests."
)
def logout_endpoint(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    actual_token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            actual_token = parts[1]
    if actual_token:
        revoke_token(token=actual_token, db=db, user=current_user)
    return {"status": "success", "message": "Successfully logged out. Session token has been revoked."}


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User",
    description="Authenticates platform users (BUILDER, ADVISOR, ADMIN) using email and password. Returns JWT bearer access token."
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return authenticate_user(db=db, request=request)

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Registers a new user (BUILDER, ADVISOR, ADMIN) and returns JWT bearer access token."
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db=db, request=request)

@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change Authenticated User Password",
    description="Verifies current credentials and securely updates password with bcrypt hash in PostgreSQL."
)
def change_password_endpoint(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return change_user_password(db=db, user=current_user, request=request)

@router.post(
    "/password-reset-request",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    description="Anti-enumeration safe password recovery endpoint reporting truthful delivery configuration status."
)
def password_reset_endpoint(
    request: PasswordResetRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    client_ip = http_request.client.host if http_request.client else "127.0.0.1"
    forwarded = http_request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    return request_password_reset(db=db, request=request, client_ip=client_ip)

@router.post(
    "/password-reset-confirm",
    status_code=status.HTTP_200_OK,
    summary="Confirm Password Reset",
    description="Validates single-use reset token and updates user password securely in PostgreSQL."
)
def password_reset_confirm_endpoint(
    request: PasswordResetConfirmRequest,
    db: Session = Depends(get_db)
):
    return confirm_password_reset(db=db, request=request)

