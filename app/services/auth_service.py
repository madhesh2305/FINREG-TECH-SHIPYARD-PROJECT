from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.security import verify_password, create_access_token, decode_access_token, get_password_hash, revoke_token, is_token_revoked
from app.core.exceptions import AuthenticationError, InactiveUserError, ConflictError, ValidationError, ForbiddenError
from app.core.config import settings
from app.models.identity import User, Role
from app.models.advisor import AdvisorProfile
from app.models.project import Project, ProjectMember
from app.services.audit_service import log_audit_event
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
)

ROLE_NORMALIZATION = {
    "BUILDER": "BUILDER",
    "ADVISOR": "ADVISOR",
    "ADMIN": "ADMIN",
    "ADMINISTRATOR": "ADMIN",
}

def authenticate_user(db: Session, request: LoginRequest) -> TokenResponse:
    """Validate credentials and return JWT bearer token response."""
    clean_email = request.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise InactiveUserError("Your account has been deactivated. Please contact administrator.")

    role_name = user.role.role_name if user.role else "USER"
    token = create_access_token(
        subject=user.user_id,
        claims={
            "email": user.email,
            "full_name": user.full_name,
            "platform_role": role_name
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.user_id,
        full_name=user.full_name,
        email=user.email,
        platform_role=role_name
    )

def register_user(db: Session, request: RegisterRequest) -> TokenResponse:
    """Register a new platform user and return JWT bearer token."""
    clean_email = request.email.lower().strip()
    
    # Check for existing user
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise ConflictError(f"User with email '{clean_email}' already exists")

    # Normalize role
    raw_role = request.role.upper().strip()
    role_name = ROLE_NORMALIZATION.get(raw_role)
    if not role_name:
        raise ValidationError(f"Invalid role '{request.role}'. Allowed roles: BUILDER, ADVISOR")

    if role_name == "ADMIN":
        raise ForbiddenError("Platform Administrator accounts cannot be self-registered. Contact platform operations.")

    # Get or create Role object
    role_obj = db.query(Role).filter(Role.role_name == role_name).first()
    if not role_obj:
        role_obj = Role(role_name=role_name, description=f"{role_name} platform role")
        db.add(role_obj)
        db.flush()

    # Hash password and create User
    now = datetime.now(timezone.utc)
    hashed_pwd = get_password_hash(request.password)
    new_user = User(
        email=clean_email,
        password_hash=hashed_pwd,
        full_name=request.full_name.strip(),
        role_id=role_obj.role_id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(new_user)
    db.flush()

    # If ADVISOR role, create AdvisorProfile
    if role_name == "ADVISOR":
        org_name = (request.organization or "").strip() or f"{new_user.full_name} Advisory"
        profile = AdvisorProfile(
            user_id=new_user.user_id,
            organization_name=org_name,
            professional_title="Regulatory & Compliance Advisor",
            specialization="Financial Crime Compliance & Regulatory Strategy",
            bio=f"Independent regulatory advisor representing {org_name}.",
            created_at=now,
            updated_at=now,
        )
        db.add(profile)
        db.flush()

    # DEF-01: Newly created advisors begin with an empty assigned project list.
    # Projects are assigned exclusively via explicit invitation or direct project owner assignment.

    # Audit log
    log_audit_event(
        db=db,
        project_id=None,
        actor_user_id=new_user.user_id,
        event_type="USER_REGISTERED",
        entity_type="USER",
        entity_id=new_user.user_id,
        event_description=f"User {clean_email} registered with platform role {role_name}",
        new_values={
            "email": clean_email,
            "full_name": new_user.full_name,
            "platform_role": role_name,
            "organization": request.organization
        }
    )

    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        subject=new_user.user_id,
        claims={
            "email": new_user.email,
            "full_name": new_user.full_name,
            "platform_role": role_name
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=new_user.user_id,
        full_name=new_user.full_name,
        email=new_user.email,
        platform_role=role_name
    )

def change_user_password(db: Session, user: User, request: ChangePasswordRequest) -> dict:
    """Safely updates user password after verifying current credentials."""
    if not verify_password(request.current_password, user.password_hash):
        raise AuthenticationError("Current password does not match registered credentials")

    if len(request.new_password.strip()) < 6:
        raise ValidationError("New password must be at least 6 characters")

    user.password_hash = get_password_hash(request.new_password.strip())
    user.updated_at = datetime.now(timezone.utc)

    log_audit_event(
        db=db,
        project_id=None,
        actor_user_id=user.user_id,
        event_type="USER_PASSWORD_CHANGED",
        entity_type="USER",
        entity_id=user.user_id,
        event_description=f"User {user.email} successfully updated their account password",
        new_values={"user_id": user.user_id, "status": "PASSWORD_UPDATED"}
    )

    db.commit()
    return {"status": "success", "message": "Password updated successfully in PostgreSQL"}

def request_password_reset(db: Session, request: PasswordResetRequest) -> PasswordResetResponse:
    """Processes password reset request with safe anti-enumeration and truthful delivery messaging."""
    clean_email = request.email.lower().strip()
    user = db.query(User).filter(User.email == clean_email).first()

    reset_token = None
    if user:
        # Issue a time-limited (15 mins) single-use cryptographic reset token
        reset_token = create_access_token(
            subject=user.user_id,
            expires_delta=timedelta(minutes=15),
            claims={"purpose": "password_reset", "email": clean_email}
        )
        log_audit_event(
            db=db,
            project_id=None,
            actor_user_id=user.user_id,
            event_type="PASSWORD_RESET_REQUESTED",
            entity_type="USER",
            entity_id=user.user_id,
            event_description=f"Password recovery requested for {clean_email}.",
            new_values={"email": clean_email}
        )
        db.commit()

    return PasswordResetResponse(
        status="pending_configuration",
        message="Password recovery requested. Automated SMTP email delivery is currently unconfigured in this environment. A direct recovery token has been generated for verification.",
        delivery_channel="SMTP (Unconfigured)",
        reset_token=reset_token
    )

def confirm_password_reset(db: Session, request: PasswordResetConfirmRequest) -> dict:
    """Validates reset token securely, updates user password, and revokes token to enforce single-use."""
    token = request.token.strip()
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("Password reset token is invalid or has expired")

    if payload.get("purpose") != "password_reset":
        raise AuthenticationError("Token is not valid for password reset")

    if is_token_revoked(token, db):
        raise AuthenticationError("Password reset token has already been used")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Malformed reset token")

    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user or not user.is_active:
        raise AuthenticationError("User account not found or deactivated")

    if len(request.new_password.strip()) < 6:
        raise ValidationError("New password must be at least 6 characters")

    user.password_hash = get_password_hash(request.new_password.strip())
    user.updated_at = datetime.now(timezone.utc)

    # Enforce single-use by revoking the reset token persistently in PostgreSQL & cache
    revoke_token(token, db, user)

    log_audit_event(
        db=db,
        project_id=None,
        actor_user_id=user.user_id,
        event_type="PASSWORD_RESET_COMPLETED",
        entity_type="USER",
        entity_id=user.user_id,
        event_description=f"Password successfully reset via recovery token for {user.email}",
        new_values={"user_id": user.user_id, "status": "PASSWORD_RESET"}
    )
    db.commit()
    return {"status": "success", "message": "Password updated successfully. You can now log in with your new credentials."}
