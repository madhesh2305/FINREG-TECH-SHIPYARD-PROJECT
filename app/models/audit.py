from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, PK_BIGINT

class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = {"schema": "audit"}

    audit_event_id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("project_management.projects.project_id"), nullable=False, index=True)
    actor_user_id = Column(BigInteger, ForeignKey("identity.users.user_id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    old_values = Column(JSON, default=dict, nullable=False)
    new_values = Column(JSON, default=dict, nullable=False)
    event_description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    project = relationship("Project", back_populates="audit_events")
    actor = relationship("User", foreign_keys=[actor_user_id])
