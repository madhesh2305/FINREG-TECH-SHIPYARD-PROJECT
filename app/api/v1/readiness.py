from typing import List, Optional, Union
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.identity import User
from app.models.project import ProjectMember
from app.models.regulatory import RegulatoryRequirement
from app.models.advice import Advice
from app.models.decision import Decision
from app.models.readiness import ReadinessItem
from app.security.authentication import get_current_user
from app.security.authorization import require_project_member

router = APIRouter(prefix="/projects/{projectId}/readiness", tags=["Audit Readiness"])

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get Project Audit Readiness Assessment",
    description="Computes Week 6 audit readiness score, governance completion metrics, and traceable evidentiary defense."
)
def get_project_readiness(
    projectId: Union[int, str],
    membership: ProjectMember = Depends(require_project_member),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pid = membership.project_id
    
    # 1. Query real DB metrics
    reqs = db.query(RegulatoryRequirement).filter(RegulatoryRequirement.project_id == pid).all()
    advices = db.query(Advice).filter(Advice.project_id == pid).all()
    decisions = db.query(Decision).filter(Decision.project_id == pid).all()
    readiness_db_items = db.query(ReadinessItem).filter(ReadinessItem.project_id == pid).all()

    total_reqs = len(reqs)
    completed_reqs = sum(1 for r in reqs if getattr(r, 'requirement_status', '') == "COMPLETED")
    
    total_advice = len(advices)
    reviewed_advice = sum(1 for a in advices if getattr(a, 'advice_status', '') in ("REVIEWED", "ACCEPTED", "SUBMITTED"))

    total_decisions = len(decisions)
    accepted_decisions = sum(1 for d in decisions if getattr(d, 'decision_type', '') in ("ACCEPT", "PROCEED", "CONDITIONAL_APPROVAL"))

    # Calculate overall readiness percentage strictly derived from persisted evidence
    # Weighting: Requirements (50%), Advisor Reviews (25%), Ratified Decisions (25%)
    req_score = (completed_reqs / total_reqs * 50) if total_reqs > 0 else 0.0
    adv_score = (reviewed_advice / total_advice * 25) if total_advice > 0 else 0.0
    dec_score = (accepted_decisions / total_decisions * 25) if total_decisions > 0 else 0.0
    readiness_pct = round(req_score + adv_score + dec_score)

    readiness_status = "AUDIT_READY" if readiness_pct >= 80 else ("IN_PROGRESS" if readiness_pct >= 50 else "ACTION_REQUIRED")

    items = [
        {
            "category": "Regulatory Obligations",
            "metric": f"{completed_reqs} of {total_reqs} Requirements Completed",
            "completion_pct": round(completed_reqs / total_reqs * 100) if total_reqs > 0 else 0,
            "status": "PASS" if completed_reqs == total_reqs and total_reqs > 0 else ("ACTION_REQUIRED" if total_reqs == 0 else "IN_PROGRESS")
        },
        {
            "category": "Advisor Governance & Review",
            "metric": f"{reviewed_advice} of {total_advice} Reviews Finalized",
            "completion_pct": round(reviewed_advice / total_advice * 100) if total_advice > 0 else 0,
            "status": "PASS" if reviewed_advice == total_advice and total_advice > 0 else ("ACTION_REQUIRED" if total_advice == 0 else "IN_PROGRESS")
        },
        {
            "category": "Binding Compliance Decisions",
            "metric": f"{accepted_decisions} of {total_decisions} Decisions Ratified",
            "completion_pct": round(accepted_decisions / total_decisions * 100) if total_decisions > 0 else 0,
            "status": "PASS" if accepted_decisions == total_decisions and total_decisions > 0 else ("ACTION_REQUIRED" if total_decisions == 0 else "IN_PROGRESS")
        }
    ]

    return {
        "project_id": pid,
        "readiness_score": f"{readiness_pct}%",
        "readiness_percentage": readiness_pct,
        "readiness_status": readiness_status,
        "summary": f"Audit readiness is currently at {readiness_pct}%. Compliance obligations, advisor reviews, and executive decisions are recorded in PostgreSQL.",
        "breakdown": items,
        "total_requirements": total_reqs,
        "completed_requirements": completed_reqs,
        "total_advice_reviews": total_advice,
        "total_decisions": total_decisions,
        "last_evaluated": "2026-10-11T12:00:00Z"
    }
