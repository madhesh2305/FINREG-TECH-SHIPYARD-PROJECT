from datetime import datetime, date, timezone
from sqlalchemy import BigInteger, Column, Date, DateTime, ForeignKey, String, Text, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class ReadinessItem(Base):
    __tablename__ = "readiness_items"
    __table_args__ = (
        CheckConstraint("priority IN ('LOW', 'MEDIUM', 'HIGH')", name="chk_readiness_priority"),
        CheckConstraint("status IN ('OPEN', 'BLOCKED', 'COMPLETED', 'NOT_APPLICABLE')", name="chk_readiness_status"),
        {"schema": "readiness"}
    )

    readiness_item_id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    requirement_id = Column(BigInteger, ForeignKey("regulatory.regulatory_requirements.requirement_id"), nullable=True)
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="OPEN", nullable=False)
    priority = Column(String(20), default="MEDIUM", nullable=False)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
