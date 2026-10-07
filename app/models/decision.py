from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Decision(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        CheckConstraint("decision_type IN ('ACCEPT', 'REJECT', 'REVIEW_REQUIRED', 'FOLLOW_UP_REQUIRED')", name="chk_decision_type"),
        {"schema": "decision"}
    )

    decision_id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    conflict_gap_id = Column(BigInteger, ForeignKey("ai.conflict_gaps.conflict_gap_id"), nullable=True)
    decided_by = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False)
    decision_type = Column(String(50), nullable=False)
    decision_rationale = Column(Text, nullable=False)
    follow_up_action = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    decider = relationship("User")
