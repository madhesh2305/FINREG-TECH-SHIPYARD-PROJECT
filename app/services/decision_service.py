from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import NotFoundError, ValidationError
from app.models.identity import User
from app.models.decision import Decision
from app.schemas.decision import (
    DecisionCreate,
    DecisionResponse,
    DECISION_TYPE_NORMALIZATION,
    VALID_DECISION_TYPES,
)
from app.services.audit_service import log_audit_event
from app.security.authorization import verify_object_belongs_to_project

def _map_decision_to_response(decision: Decision, db: Session) -> DecisionResponse:
    decider = db.query(User).filter(User.user_id == decision.decided_by).first()
    return DecisionResponse(
        decision_id=decision.decision_id,
        project_id=decision.project_id,
        conflict_gap_id=decision.conflict_gap_id,
        decided_by=decision.decided_by,
        decider_name=decider.full_name if decider else None,
        decider_email=decider.email if decider else None,
        decision_type=decision.decision_type,
        decision_rationale=decision.decision_rationale,
        follow_up_action=decision.follow_up_action,
        created_at=decision.created_at,
    )

def record_decision(db: Session, project_id: int, request: DecisionCreate, actor: User) -> DecisionResponse:
    """Record an authoritative compliance decision for a project (Owner only)."""
    raw_type = request.decision_type.upper().strip()
    norm_type = DECISION_TYPE_NORMALIZATION.get(raw_type)
    if not norm_type or norm_type not in VALID_DECISION_TYPES:
        raise ValidationError(
            f"Invalid decision type '{request.decision_type}'. Allowed types: {', '.join(VALID_DECISION_TYPES)}"
        )

    now = datetime.now(timezone.utc)
    decision = Decision(
        project_id=project_id,
        conflict_gap_id=request.conflict_gap_id,
        decided_by=actor.user_id,
        decision_type=norm_type,
        decision_rationale=request.decision_rationale.strip(),
        follow_up_action=request.follow_up_action.strip() if request.follow_up_action else None,
        created_at=now,
    )
    db.add(decision)
    db.flush()

    # Log immutable audit event
    log_audit_event(
        db=db,
        project_id=project_id,
        actor_user_id=actor.user_id,
        event_type="DECISION_RECORDED",
        entity_type="DECISION",
        entity_id=decision.decision_id,
        event_description=f"Compliance decision '{norm_type}' recorded by {actor.full_name}",
        new_values={
            "decision_id": decision.decision_id,
            "decision_type": norm_type,
            "rationale": decision.decision_rationale,
            "follow_up_action": decision.follow_up_action,
            "conflict_gap_id": decision.conflict_gap_id,
        },
    )

    db.commit()
    db.refresh(decision)
    return _map_decision_to_response(decision, db)

def list_project_decisions(db: Session, project_id: int) -> List[DecisionResponse]:
    """List all decisions recorded for a project."""
    decisions = (
        db.query(Decision)
        .filter(Decision.project_id == project_id)
        .order_by(Decision.created_at.desc())
        .all()
    )
    return [_map_decision_to_response(d, db) for d in decisions]

def get_decision_by_id(db: Session, project_id: int, decision_id: int) -> DecisionResponse:
    """Retrieve single decision with BOLA check."""
    decision = db.query(Decision).filter(Decision.decision_id == decision_id).first()
    if not decision:
        raise NotFoundError(f"Decision with ID {decision_id} not found")
    verify_object_belongs_to_project(decision.project_id, project_id, "Decision")
    return _map_decision_to_response(decision, db)
