from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

VALID_DECISION_TYPES = ["ACCEPT", "REJECT", "REVIEW_REQUIRED", "FOLLOW_UP_REQUIRED"]

DECISION_TYPE_NORMALIZATION = {
    "ACCEPT": "ACCEPT",
    "ACCEPTED": "ACCEPT",
    "REJECT": "REJECT",
    "REJECTED": "REJECT",
    "REVIEW_REQUIRED": "REVIEW_REQUIRED",
    "REVIEW REQUIRED": "REVIEW_REQUIRED",
    "NEEDS REVIEW": "REVIEW_REQUIRED",
    "FOLLOW_UP_REQUIRED": "FOLLOW_UP_REQUIRED",
    "FOLLOW UP REQUIRED": "FOLLOW_UP_REQUIRED",
    "FOLLOW-UP REQUIRED": "FOLLOW_UP_REQUIRED",
}

class DecisionCreate(BaseModel):
    decision_type: str = Field(..., description="Decision type: ACCEPT, REJECT, REVIEW_REQUIRED, or FOLLOW_UP_REQUIRED")
    decision_rationale: str = Field(..., min_length=5, description="Executive justification and compliance reasoning")
    follow_up_action: Optional[str] = Field(None, description="Assigned action item or operational follow-up requirement")
    conflict_gap_id: Optional[int] = Field(None, description="Optional conflict or gap ID resolved by this decision")

class DecisionResponse(BaseModel):
    decision_id: int
    project_id: int
    conflict_gap_id: Optional[int] = None
    decided_by: int
    decider_name: Optional[str] = None
    decider_email: Optional[str] = None
    decision_type: str
    decision_rationale: str
    follow_up_action: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
