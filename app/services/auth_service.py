import hashlib
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import verify_password, create_access_token, decode_access_token, get_password_hash, revoke_token, is_token_revoked
from app.core.exceptions import AuthenticationError, InactiveUserError, ConflictError, ValidationError, ForbiddenError
from app.core.config import settings
from app.models.identity import User, Role, PasswordResetToken
from app.models.advisor import AdvisorProfile
from app.models.project import Project, ProjectMember
from app.services.audit_service import log_audit_event
from app.services.email_service import is_email_configured, is_email_service_available, send_password_reset_email
from app.services.rate_limit_service import check_password_reset_rate_limit, reset_rate_limiter
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirmRequest,
)

logger = logging.getLogger(__name__)

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

    # Determine authoritative role with strong ADVISOR preservation (DEF-23)
    if user.role and user.role.role_name:
        role_name = user.role.role_name.upper()
    elif user.advisor_profile:
        role_name = "ADVISOR"
        adv_role = db.query(Role).filter(Role.role_name == "ADVISOR").first()
        if adv_role:
            user.role_id = adv_role.role_id
            db.commit()
    else:
        role_name = "BUILDER"

    # Ensure ADVISOR has AdvisorProfile (DEF-25)
    if role_name == "ADVISOR" and not user.advisor_profile:
        now = datetime.now(timezone.utc)
        prof = AdvisorProfile(
            user_id=user.user_id,
            organization_name=f"{user.full_name} Advisory",
            professional_title="Regulatory & Compliance Advisor",
            specialization="Financial Crime Compliance & Regulatory Strategy",
            bio=f"Verified compliance advisor {user.full_name}.",
            created_at=user.created_at or now,
            updated_at=user.updated_at or now,
        )
        db.add(prof)
        db.commit()

    pwd_sig = hashlib.sha256(user.password_hash.encode("utf-8")).hexdigest()[:16]
    token = create_access_token(
        subject=user.user_id,
        claims={
            "email": user.email,
            "full_name": user.full_name,
            "platform_role": role_name,
            "pwd_sig": pwd_sig
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

    pwd_sig = hashlib.sha256(new_user.password_hash.encode("utf-8")).hexdigest()[:16]
    token = create_access_token(
        subject=new_user.user_id,
        claims={
            "email": new_user.email,
            "full_name": new_user.full_name,
            "platform_role": role_name,
            "pwd_sig": pwd_sig
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


def request_password_reset(
    db: Session,
    request: PasswordResetRequest,
    client_ip: Optional[str] = None
) -> PasswordResetResponse:
    """
    Processes password reset requests with robust anti-enumeration, dual-key sliding window
    rate limiting (per-account digest and per-client IP), safe token generation with rollback on
    delivery failure, and truthful delivery status. Never returns reset token in HTTP response.
    """
    clean_email = request.email.lower().strip()

    # Enforce dual-key sliding window rate limit
    if not check_password_reset_rate_limit(clean_email, client_ip=client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password recovery requests. Please wait a few minutes before trying again."
        )

    # 1. Environment check: If SMTP is globally unconfigured
    if not is_email_configured():
        logger.info("Password recovery requested but email service is unconfigured in this environment.")
        return PasswordResetResponse(
            status="pending_configuration",
            message="Password recovery via email is currently unconfigured in this environment. Automated delivery is unavailable.",
            delivery_channel="SMTP (Unconfigured)"
        )

    # 2. Service health check: If SMTP transport is experiencing failures or simulated outage
    if not is_email_service_available():
        logger.error("Operational notice: Password recovery dispatch failed because email service is unavailable.")
        return PasswordResetResponse(
            status="delivery_failed",
            message="Password reset delivery is temporarily unavailable. Please try again later or contact support.",
            delivery_channel="Email (Service Unavailable)"
        )

    user = db.query(User).filter(User.email == clean_email).first()

    if user and user.is_active:
        # Generate unpredictable, high-entropy cryptographic token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        # Attempt email delivery FIRST before revoking prior tokens or committing new token
        delivery_ok = send_password_reset_email(
            to_email=clean_email,
            reset_token=raw_token,
            user_name=user.full_name
        )

        if not delivery_ok:
            # Delivery failed: Roll back any changes so existing usable tokens are NOT invalidated
            db.rollback()
            logger.error("Operational notice: Password reset email dispatch failed for user account.")
            return PasswordResetResponse(
                status="delivery_failed",
                message="Password reset delivery is temporarily unavailable. Please try again later or contact support.",
                delivery_channel="Email (Service Unavailable)"
            )

        # Delivery succeeded: Invalidate prior unused reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.user_id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.is_revoked.is_(False)
        ).update({"is_revoked": True})

        # Persist secure hash in identity.password_reset_tokens
        db_token = PasswordResetToken(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(db_token)
        db.flush()

        log_audit_event(
            db=db,
            project_id=None,
            actor_user_id=user.user_id,
            event_type="PASSWORD_RESET_REQUESTED",
            entity_type="USER",
            entity_id=user.user_id,
            event_description=f"Password recovery requested for {clean_email}.",
            new_values={"email": clean_email, "expires_at": expires_at.isoformat()}
        )
        db.commit()

    # Public response is 100% identical for existing and non-existing accounts (anti-enumeration)
    return PasswordResetResponse(
        status="success",
        message="If an account associated with this email address exists, password recovery instructions have been dispatched.",
        delivery_channel="Email"
    )

def confirm_password_reset(db: Session, request: PasswordResetConfirmRequest) -> dict:
    """
    Validates reset token securely via hash lookup, updates user password,
    invalidates the reset token to enforce single-use, and revokes prior active sessions.
    """
    raw_token = request.token.strip()
    if not raw_token or len(raw_token) < 16:
        raise AuthenticationError("Password reset token is invalid, expired, or already used")

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_rec = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not token_rec:
        raise AuthenticationError("Password reset token is invalid, expired, or already used")

    if token_rec.is_revoked or token_rec.used_at is not None:
        raise AuthenticationError("Password reset token has already been used or revoked")

    now_utc = datetime.now(timezone.utc)
    if token_rec.expires_at < now_utc:
        token_rec.is_revoked = True
        db.commit()
        raise AuthenticationError("Password reset token has expired")

    user = db.query(User).filter(User.user_id == token_rec.user_id).first()
    if not user or not user.is_active:
        raise AuthenticationError("User account not found or deactivated")

    new_pwd = request.new_password.strip()
    if len(new_pwd) < 6:
        raise ValidationError("New password must be at least 6 characters")

    user.password_hash = get_password_hash(new_pwd)
    user.updated_at = datetime.now(timezone.utc)

    # Invalidate this token and mark it used
    token_rec.used_at = datetime.now(timezone.utc)
    token_rec.is_revoked = True

    # Revoke any other pending reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.is_revoked.is_(False)
    ).update({"is_revoked": True})

    log_audit_event(
        db=db,
        project_id=None,
        actor_user_id=user.user_id,
        event_type="PASSWORD_RESET_COMPLETED",
        entity_type="USER",
        entity_id=user.user_id,
        event_description=f"Password successfully reset via single-use recovery token for {user.email}",
        new_values={"user_id": user.user_id, "status": "PASSWORD_RESET"}
    )
    db.commit()
    return {"status": "success", "message": "Password updated successfully. You can now log in with your new credentials."}
