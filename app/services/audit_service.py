from typing import Any, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent

SENSITIVE_KEYS = {"password", "password_hash", "token", "secret", "credentials", "access_token"}

def sanitize_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Sanitize audit payload to remove passwords, tokens, and secrets."""
    if not payload:
        return {}
    sanitized = {}
    for k, v in payload.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload(v)
        else:
            sanitized[k] = v
    return sanitized

def log_audit_event(
    db: Session,
    project_id: int,
    actor_user_id: int,
    event_type: str,
    entity_type: str,
    entity_id: int,
    event_description: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    """Log an immutable material audit event to audit.audit_events."""
    event = AuditEvent(
        project_id=project_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=sanitize_payload(old_values),
        new_values=sanitize_payload(new_values),
        event_description=event_description,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()
    return event


def list_project_audit_events(
    db: Session,
    project_id: int,
    event_type: Optional[str] = None,
    limit: int = 100
) -> list[AuditEvent]:
    query = db.query(AuditEvent).filter(AuditEvent.project_id == project_id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
