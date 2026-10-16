import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Set, Union
import bcrypt
import jwt
from sqlalchemy.orm import Session
from app.core.config import settings

# Thread-safe in-memory cache of revoked token signatures
_REVOKED_TOKEN_SIGNATURES: Set[str] = set()

def get_password_hash(password: str) -> str:
    """Hash plaintext password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None, claims: Optional[dict] = None) -> str:
    """Issue JWT access token with expiry, unique jti, and claims."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "jti": str(uuid.uuid4())
    }
    if claims:
        to_encode.update(claims)
        
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        return None

def compute_token_signature(token: str) -> str:
    """Computes a SHA-256 fingerprint for a token to track revocation."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

def revoke_token(token: str, db: Session, user: Optional[Any] = None) -> None:
    """Revokes a JWT token persistently in PostgreSQL and registers in-memory cache."""
    from app.models.identity import RevokedToken
    from app.services.audit_service import log_audit_event

    sig = compute_token_signature(token)
    _REVOKED_TOKEN_SIGNATURES.add(sig)

    payload = decode_access_token(token)
    jti = payload.get("jti") if payload else None
    exp_ts = payload.get("exp") if payload else None
    expires_at = datetime.fromtimestamp(exp_ts, timezone.utc) if exp_ts else None

    # Check if already persisted
    existing = db.query(RevokedToken).filter(RevokedToken.token_signature == sig).first()
    if not existing:
        revoked_rec = RevokedToken(
            jti=jti,
            token_signature=sig,
            revoked_at=datetime.now(timezone.utc),
            expires_at=expires_at
        )
        db.add(revoked_rec)
        db.flush()

    if user:
        log_audit_event(
            db=db,
            project_id=None,
            actor_user_id=getattr(user, "user_id", None),
            event_type="USER_LOGOUT",
            entity_type="SESSION",
            entity_id=getattr(user, "user_id", 0),
            event_description=f"User session terminated and JWT token revoked for {getattr(user, 'email', 'user')}",
            new_values={"token_signature_prefix": sig[:12], "revoked": True}
        )

    db.commit()

def is_token_revoked(token: str, db: Session) -> bool:
    """Checks whether a token has been explicitly revoked via cache or PostgreSQL."""
    from app.models.identity import RevokedToken

    sig = compute_token_signature(token)
    if sig in _REVOKED_TOKEN_SIGNATURES:
        return True

    # Query PostgreSQL
    existing = db.query(RevokedToken).filter(RevokedToken.token_signature == sig).first()
    if existing:
        _REVOKED_TOKEN_SIGNATURES.add(sig)
        return True

    return False
