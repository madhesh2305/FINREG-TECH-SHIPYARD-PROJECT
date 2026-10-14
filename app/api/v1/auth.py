from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetResponse
)
from app.services.auth_service import (
    authenticate_user,
    register_user,
    change_user_password,
    request_password_reset
)
from app.security.authentication import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
    db: Session = Depends(get_db)
):
    return request_password_reset(db=db, request=request)

