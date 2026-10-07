from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import authenticate_user, register_user

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

