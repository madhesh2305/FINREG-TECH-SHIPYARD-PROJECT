from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, InactiveUserError
from app.db.session import get_db
from app.models.identity import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    authorization: str = Header(None)
) -> User:
    """Dependency that authenticates JWT token and returns active User."""
    actual_token = token
    if not actual_token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            actual_token = parts[1]

    if not actual_token:
        raise AuthenticationError("Authentication token is missing")

    payload = decode_access_token(actual_token)
    if not payload or "sub" not in payload:
        raise AuthenticationError("Invalid or expired authentication token")

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise AuthenticationError("Malformed user identifier in token")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise AuthenticationError("User associated with token no longer exists")

    if not user.is_active:
        raise InactiveUserError("User account has been deactivated")

    return user
